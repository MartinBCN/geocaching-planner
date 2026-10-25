import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from geocaching_planner.config import AppConfig
from geocaching_planner.main import create_app


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Clear GCP_* overrides and run from an empty directory so no real .env is read."""
    for name in [key for key in os.environ if key.startswith("GCP_")]:
        monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def config() -> AppConfig:
    return AppConfig(_env_file=None)


@pytest.fixture
def app(config: AppConfig) -> FastAPI:
    return create_app(config)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
async def lenient_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client that returns 500 responses instead of re-raising unhandled app exceptions."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
