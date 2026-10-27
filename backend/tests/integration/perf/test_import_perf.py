import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.api.deps import get_session
from geocaching_planner.config import AppConfig
from geocaching_planner.main import create_app
from tests.conftest import FakeProbe
from tests.fixtures.pq.generate import make_pq


@asynccontextmanager
async def _client(config: AppConfig, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(config, database_probe=FakeProbe())

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.slow
async def test_imports_one_thousand_synthetic_caches_under_ten_seconds(
    config: AppConfig, db_session: AsyncSession
) -> None:
    gpx = make_pq(1000)
    started = time.perf_counter()
    async with _client(config, db_session) as client:
        response = await client.post(
            "/api/v1/imports",
            files=[("files", ("performance.gpx", gpx, "application/gpx+xml"))],
        )
    elapsed = time.perf_counter() - started

    assert response.status_code == 201
    assert response.json()["created"] == 1000
    assert elapsed < 10, f"Import took {elapsed:.2f} seconds."
