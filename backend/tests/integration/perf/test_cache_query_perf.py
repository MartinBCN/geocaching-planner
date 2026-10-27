import math
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.models import CacheModel, UserCacheDataModel
from geocaching_planner.adapters.db.spatial import coordinates_to_point
from geocaching_planner.api.deps import get_session
from geocaching_planner.api.routes.caches import MARKER_CAP
from geocaching_planner.config import AppConfig
from geocaching_planner.domain.cache import CacheType
from geocaching_planner.main import create_app
from tests.conftest import FakeProbe
from tests.fixtures.cache_factory import make_caches


@asynccontextmanager
async def _client(config: AppConfig, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(config, database_probe=FakeProbe())

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.slow
async def test_marker_query_50k_cache_latency_and_both_spatial_indexes(
    config: AppConfig, db_session: AsyncSession
) -> None:
    caches = make_caches(50_000, seed=17)
    await db_session.execute(
        insert(CacheModel),
        [
            {
                "gc_code": cache.gc_code,
                "name": cache.name,
                "type": cache.type.value,
                "source_type": cache.source_type,
                "container": cache.container.value,
                "source_container": cache.source_container,
                "difficulty": cache.difficulty,
                "terrain": cache.terrain,
                "owner": cache.owner,
                "placed_at": cache.placed_at,
                "location": coordinates_to_point(cache.location),
                "country": cache.country,
                "state": cache.state,
                "short_description": cache.short_description,
                "long_description": cache.long_description,
                "description_is_html": cache.description_is_html,
                "hint": cache.hint,
                "attributes": [],
                "is_available": cache.is_available,
                "is_archived": cache.is_archived,
                "found_by_me": cache.found_by_me,
                "found_at": cache.found_at,
                "source": cache.source,
                "source_updated_at": cache.source_updated_at,
                "source_hash": cache.source_hash,
            }
            for cache in caches
        ],
    )
    await db_session.execute(
        insert(UserCacheDataModel),
        [
            {
                "cache_gc_code": cache.gc_code,
                "note": "",
                "corrected_location": coordinates_to_point(cache.location),
            }
            for index, cache in enumerate(caches)
            if index % 10 == 0
        ],
    )
    await db_session.execute(text("ANALYZE caches"))
    await db_session.execute(text("ANALYZE user_cache_data"))

    plan_sql = """
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT c.gc_code,
               c.name,
               ST_Y(CAST(COALESCE(display_correction.corrected_location, c.location) AS geometry)),
               ST_X(CAST(COALESCE(display_correction.corrected_location, c.location) AS geometry)),
               c.type,
               c.container,
               c.difficulty,
               c.terrain,
               c.found_by_me,
               c.is_available,
               c.is_archived,
               display_correction.corrected_location IS NOT NULL
        FROM caches AS c
        LEFT JOIN user_cache_data AS display_correction
          ON display_correction.cache_gc_code = c.gc_code
        WHERE c.type = 'Traditional'
          AND c.found_by_me IS FALSE
          AND c.is_archived IS FALSE
          AND c.gc_code IN (
            SELECT u.cache_gc_code
            FROM user_cache_data AS u
            WHERE u.corrected_location IS NOT NULL
              AND CAST(u.corrected_location AS geometry(GEOMETRY))
                  && ST_MakeEnvelope(4.25, 51.75, 4.75, 52.25, 4326)
              AND ST_Intersects(
                  CAST(u.corrected_location AS geometry(GEOMETRY)),
                  ST_MakeEnvelope(4.25, 51.75, 4.75, 52.25, 4326)
              )
            UNION ALL
            SELECT original.gc_code
            FROM caches AS original
            LEFT JOIN user_cache_data AS correction
              ON correction.cache_gc_code = original.gc_code
            WHERE correction.corrected_location IS NULL
              AND CAST(original.location AS geometry(GEOMETRY))
                  && ST_MakeEnvelope(4.25, 51.75, 4.75, 52.25, 4326)
              AND ST_Intersects(
                  CAST(original.location AS geometry(GEOMETRY)),
                  ST_MakeEnvelope(4.25, 51.75, 4.75, 52.25, 4326)
              )
          )
        ORDER BY c.gc_code
        LIMIT :cap
    """
    plan_rows = await db_session.execute(
        text(plan_sql),
        {"cap": MARKER_CAP},
    )
    plan = "\n".join(row[0] for row in plan_rows)
    assert "ix_caches_location_geometry_gist" in plan, plan
    assert "ix_user_cache_data_corrected_geometry_gist" in plan, plan
    params = (
        ("bbox", "4.25,51.75,4.75,52.25"),
        ("types", CacheType.TRADITIONAL.value),
        ("found", "false"),
    )
    async with _client(config, db_session) as client:
        timings: list[float] = []
        for _ in range(20):
            started = time.perf_counter()
            response = await client.get("/api/v1/caches/markers", params=params)
            timings.append(time.perf_counter() - started)
            assert response.status_code == 200
            assert 1_900 <= response.json()["total"] <= 2_100

    p95 = sorted(timings)[math.ceil(0.95 * len(timings)) - 1]
    assert p95 < 0.3, f"Marker query p95 was {p95 * 1000:.1f} ms."
