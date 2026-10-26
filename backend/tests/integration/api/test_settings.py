from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.api.deps import get_session
from geocaching_planner.config import AppConfig
from geocaching_planner.main import create_app
from tests.conftest import FakeProbe

DEFAULT_SETTINGS = {
    "home_location": None,
    "avg_speed_kmh": 18,
    "corridor_m_default": 500,
    "default_profile": "trekking",
    "tile_url": "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
    "tile_attribution": "© OpenStreetMap contributors, CyclOSM",
}


@asynccontextmanager
async def _client(config: AppConfig, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(config, database_probe=FakeProbe())

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_get_returns_defaults_on_fresh_database(
    config: AppConfig, db_session: AsyncSession
) -> None:
    async with _client(config, db_session) as client:
        response = await client.get("/api/v1/settings")
        assert response.status_code == 200
        assert response.json() == DEFAULT_SETTINGS


async def test_put_persists_settings(config: AppConfig, db_session: AsyncSession) -> None:
    async with _client(config, db_session) as client:
        updated = {
            **DEFAULT_SETTINGS,
            "home_location": {"lat": 52.1, "lon": 4.3},
            "avg_speed_kmh": 22,
            "corridor_m_default": 750,
            "default_profile": "safety",
            "tile_url": "https://tiles.example/{z}/{x}/{y}.png",
            "tile_attribution": "Example tiles",
        }
        put_response = await client.put("/api/v1/settings", json=updated)
        get_response = await client.get("/api/v1/settings")

        assert put_response.status_code == 200
        assert put_response.json() == updated
        assert get_response.status_code == 200
        assert get_response.json() == updated


async def test_invalid_settings_return_problem_json(
    config: AppConfig, db_session: AsyncSession
) -> None:
    async with _client(config, db_session) as client:
        invalid = [
            {**DEFAULT_SETTINGS, "avg_speed_kmh": 4},
            {**DEFAULT_SETTINGS, "corridor_m_default": 5001},
            {**DEFAULT_SETTINGS, "default_profile": "car"},
            {**DEFAULT_SETTINGS, "home_location": {"lat": 91, "lon": 0}},
        ]
        for settings in invalid:
            response = await client.put("/api/v1/settings", json=settings)
            assert response.status_code == 422
            assert response.headers["content-type"].startswith("application/problem+json")
