"""Compose-stack check: the real compose.yaml database service becomes healthy and migrates.

Run with `mise run test:compose:db`. Requires Docker. Excluded from `mise run check`.
"""

import asyncio
import subprocess
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from geocaching_planner.adapters.db.migrations import alembic_config
from geocaching_planner.config import AppConfig
from geocaching_planner.devstack import DOCKER

pytestmark = [pytest.mark.compose_stack, pytest.mark.enable_socket]

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_compose_db_service_is_healthy_and_migrates() -> None:
    """AC1 (database part): the compose db service becomes healthy and migrations apply."""
    up = subprocess.run(  # noqa: S603 - fixed argv, no untrusted input
        [DOCKER, "compose", "up", "-d", "--wait", "db"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert up.returncode == 0, up.stderr

    url = AppConfig().database_url
    command.upgrade(alembic_config(url), "head")

    async def _version() -> object:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            value = (await conn.execute(text("SELECT postgis_version()"))).scalar_one()
        await engine.dispose()
        return value

    assert asyncio.run(_version())
