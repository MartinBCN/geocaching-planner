import asyncio
import shutil
import subprocess
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from geocaching_planner.adapters.db.migrations import alembic_config

IMAGE = "postgis/postgis:17-3.5"
PLATFORM = "linux/amd64"


def _pull_amd64(image: str) -> None:
    docker = shutil.which("docker") or "docker"
    result = subprocess.run(  # noqa: S603 - fixed argv, image name is a constant
        [docker, "pull", "--platform", PLATFORM, image],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"Could not pull {image} for {PLATFORM}: {result.stderr}", pytrace=False)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/integration/" in str(item.path).replace("\\", "/"):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.enable_socket)


@pytest.fixture(scope="session")
def postgis_url() -> Iterator[str]:
    """Start a throwaway PostGIS container once per session and migrate it to head."""
    # The PostGIS image publishes only amd64. testcontainers ignores the platform kwarg for
    # the pull, so pull explicitly for the compose stack's platform first.
    _pull_amd64(IMAGE)
    container = PostgresContainer(
        image=IMAGE,
        username="geocaching",
        password="geocaching",
        dbname="geocaching",
        driver="asyncpg",
    )
    try:
        container.start()
    except Exception as exc:  # Docker missing or daemon down
        pytest.fail(f"Docker is required for integration tests: {exc}", pytrace=False)
    try:
        url = container.get_connection_url()
        command.upgrade(alembic_config(url), "head")
        yield url
    finally:
        container.stop()


@pytest.fixture(scope="session")
def isolation_table(postgis_url: str) -> None:
    """Create a probe table with committed DDL so each test can verify rollback isolation."""

    async def _create() -> None:
        engine = create_async_engine(postgis_url)
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS isolation_probe (id serial PRIMARY KEY, note text)"
                )
            )
        await engine.dispose()

    asyncio.run(_create())


@pytest.fixture
async def db_session(postgis_url: str, isolation_table: None) -> AsyncIterator[AsyncSession]:
    """Session bound to a connection-level transaction that is rolled back after each test."""
    engine: AsyncEngine = create_async_engine(postgis_url)
    async with engine.connect() as conn:
        outer = await conn.begin()
        session = AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()
