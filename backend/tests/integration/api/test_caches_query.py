from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.cache_repository import SqlAlchemyCacheRepository
from geocaching_planner.adapters.db.settings_repository import SqlAlchemySettingsRepository
from geocaching_planner.api.deps import get_session
from geocaching_planner.config import AppConfig
from geocaching_planner.domain.cache import (
    Cache,
    CacheType,
    ContainerSize,
    Coordinates,
    UserCacheDataUpdate,
)
from geocaching_planner.domain.settings import PlannerSettings
from geocaching_planner.main import create_app
from tests.conftest import FakeProbe
from tests.fixtures.cache_factory import make_caches


@asynccontextmanager
async def _client(
    config: AppConfig, db_session: AsyncSession, *, marker_cap: int = 20_000
) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(config, database_probe=FakeProbe())
    app.state.marker_cap = marker_cap

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


def _cache_set() -> tuple[Cache, ...]:
    base = tuple(
        replace(cache, location=Coordinates(lat=52.1, lon=4.3)) for cache in make_caches(6)
    )
    return (
        replace(
            base[0],
            type=CacheType.TRADITIONAL,
            container=ContainerSize.MICRO,
            difficulty=1.5,
            terrain=2,
            name="Alpha pocket",
            found_by_me=False,
            is_available=True,
            is_archived=False,
        ),
        replace(
            base[1],
            type=CacheType.MYSTERY,
            container=ContainerSize.SMALL,
            difficulty=2,
            terrain=3,
            name="Other Cache",
            found_by_me=False,
            is_available=True,
            is_archived=False,
        ),
        replace(
            base[2],
            type=CacheType.MULTI,
            container=ContainerSize.REGULAR,
            difficulty=2.5,
            terrain=4,
            name="Needle ABC",
            found_by_me=False,
            is_available=True,
            is_archived=False,
        ),
        replace(
            base[3],
            type=CacheType.TRADITIONAL,
            container=ContainerSize.MICRO,
            difficulty=5,
            terrain=5,
            name="Archive candidate",
            found_by_me=True,
            is_available=False,
            is_archived=True,
        ),
        replace(
            base[4],
            type=CacheType.TRADITIONAL,
            container=ContainerSize.LARGE,
            difficulty=3,
            terrain=3,
            name="Disabled candidate",
            found_by_me=False,
            is_available=False,
            is_archived=False,
        ),
        replace(
            base[5],
            type=CacheType.MYSTERY,
            container=ContainerSize.SMALL,
            difficulty=2,
            terrain=3,
            name="ABC at the end",
            found_by_me=True,
            is_available=True,
            is_archived=False,
        ),
    )


async def _seed(session: AsyncSession, caches: tuple[Cache, ...]) -> None:
    await SqlAlchemyCacheRepository(session).upsert_many(caches)


async def test_each_filter_field_semantics(config: AppConfig, db_session: AsyncSession) -> None:
    caches = _cache_set()
    await _seed(db_session, caches)
    async with _client(config, db_session) as client:
        combined = await client.get(
            "/api/v1/caches",
            params=[
                ("types", "Traditional"),
                ("types", "Mystery"),
                ("containers", "Micro"),
                ("containers", "Small"),
                ("difficulty_min", "1.5"),
                ("difficulty_max", "2"),
                ("terrain_min", "2"),
                ("terrain_max", "3"),
                ("found", "false"),
            ],
        )
        include_disabled = await client.get(
            "/api/v1/caches",
            params={"include_disabled": "false"},
        )
        include_archived = await client.get(
            "/api/v1/caches",
            params={"include_archived": "true", "found": "true"},
        )
        text_match = await client.get("/api/v1/caches", params={"text": "abc"})
        gc_prefix_match = await client.get("/api/v1/caches", params={"text": "gc0000"})

    assert combined.status_code == 200
    assert [item["gc_code"] for item in combined.json()["items"]] == [
        "GC000000",
        "GC000001",
    ]
    assert [item["gc_code"] for item in include_disabled.json()["items"]] == [
        "GC000000",
        "GC000001",
        "GC000002",
        "GC000005",
    ]
    assert [item["gc_code"] for item in include_archived.json()["items"]] == [
        "GC000003",
        "GC000005",
    ]
    assert [item["gc_code"] for item in text_match.json()["items"]] == [
        "GC000002",
        "GC000005",
    ]
    assert len(gc_prefix_match.json()["items"]) == 5


async def test_distance_uses_effective_location(
    config: AppConfig, db_session: AsyncSession
) -> None:
    cache = make_caches(1)[0]
    await _seed(
        db_session,
        (
            replace(
                cache,
                location=Coordinates(lat=52.10898315, lon=4.3),
                is_archived=False,
            ),
        ),
    )
    await SqlAlchemySettingsRepository(db_session).save(
        PlannerSettings(home_location=Coordinates(lat=52.1, lon=4.3))
    )
    await SqlAlchemyCacheRepository(db_session).set_user_data(
        cache.gc_code,
        update=UserCacheDataUpdate(corrected_location=Coordinates(lat=52.1898315, lon=4.3)),
    )
    async with _client(config, db_session) as client:
        filtered = await client.get("/api/v1/caches", params={"max_distance_km": 5})
        unfiltered = await client.get("/api/v1/caches")

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0
    summary = unfiltered.json()["items"][0]
    assert summary["has_corrected"] is True
    assert summary["distance_km"] == pytest.approx(10, abs=0.01)


async def test_bbox_excludes_cache_moved_out_by_correction(
    config: AppConfig, db_session: AsyncSession
) -> None:
    cache = make_caches(1)[0]
    await _seed(db_session, (replace(cache, location=Coordinates(lat=52.1, lon=4.3)),))
    await SqlAlchemyCacheRepository(db_session).set_user_data(
        cache.gc_code,
        update=UserCacheDataUpdate(corrected_location=Coordinates(lat=52.1, lon=5.0)),
    )
    async with _client(config, db_session) as client:
        response = await client.get(
            "/api/v1/caches/markers",
            params={"bbox": "4,52,4.5,52.5"},
        )

    assert response.status_code == 200
    assert response.json() == {"items": [], "truncated": False, "total": 0}


async def test_paging_defaults_tiebreak_and_past_end(
    config: AppConfig, db_session: AsyncSession
) -> None:
    caches = _cache_set()
    await _seed(
        db_session,
        tuple(replace(cache, name="Same name", is_archived=False) for cache in caches),
    )
    async with _client(config, db_session) as client:
        default = await client.get("/api/v1/caches")
        page = await client.get(
            "/api/v1/caches", params={"sort": "name", "page": 2, "page_size": 2}
        )
        past_end = await client.get("/api/v1/caches", params={"page": 99, "page_size": 2})

    assert default.status_code == 200
    assert len(default.json()["items"]) == 6
    assert [item["gc_code"] for item in page.json()["items"]] == ["GC000002", "GC000003"]
    assert past_end.json() == {"items": [], "total": 6}


async def test_distance_without_home_is_problem(
    config: AppConfig, db_session: AsyncSession
) -> None:
    await _seed(db_session, (replace(make_caches(1)[0], is_archived=False),))
    async with _client(config, db_session) as client:
        filtered = await client.get("/api/v1/caches", params={"max_distance_km": 5})
        sorted_by_distance = await client.get("/api/v1/caches", params={"sort": "distance"})
        unfiltered = await client.get("/api/v1/caches")

    for response in (filtered, sorted_by_distance):
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")
        assert response.json()["type"] == "about:blank"
        assert "home location" in response.json()["detail"].lower()
    assert unfiltered.json()["items"][0]["distance_km"] is None


async def test_invalid_sort_ranges_and_bbox_are_problem(
    config: AppConfig, db_session: AsyncSession
) -> None:
    async with _client(config, db_session) as client:
        invalid_requests = [
            await client.get("/api/v1/caches", params={"sort": "unknown"}),
            await client.get("/api/v1/caches", params={"difficulty_min": 1.25}),
            await client.get("/api/v1/caches", params={"difficulty_min": 4, "difficulty_max": 3}),
            await client.get("/api/v1/caches/markers"),
            await client.get("/api/v1/caches/markers", params={"bbox": "181,0,182,1"}),
            await client.get("/api/v1/caches/markers", params={"bbox": "4,52,4,53"}),
        ]

    for response in invalid_requests:
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")


async def test_markers_have_stable_cap_and_total(
    config: AppConfig, db_session: AsyncSession
) -> None:
    await _seed(
        db_session,
        tuple(replace(cache, is_archived=False) for cache in _cache_set()),
    )
    async with _client(config, db_session, marker_cap=5) as client:
        fewer = await client.get(
            "/api/v1/caches/markers",
            params={"bbox": "4,52,5,53", "found": "false", "types": "Traditional"},
        )
        all_markers = await client.get(
            "/api/v1/caches/markers",
            params={"bbox": "4,52,5,53"},
        )

    assert fewer.status_code == 200
    assert fewer.json()["truncated"] is False
    assert fewer.json()["total"] == len(fewer.json()["items"])
    assert all(len(item) == 12 for item in fewer.json()["items"])
    assert all_markers.json()["truncated"] is True
    assert all_markers.json()["total"] == 6
    assert [item[0] for item in all_markers.json()["items"]] == [
        "GC000000",
        "GC000001",
        "GC000002",
        "GC000003",
        "GC000004",
    ]
