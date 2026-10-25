import asyncio

from alembic import command
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from geocaching_planner.adapters.db.migrations import alembic_config


def _query_scalar(url: str, sql: str) -> object:
    async def _run() -> object:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            value = (await conn.execute(text(sql))).scalar()
        await engine.dispose()
        return value

    return asyncio.run(_run())


def _recreate_database(admin_url: str, name: str) -> None:
    async def _run() -> None:
        engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        async with engine.connect() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            await conn.execute(text(f'CREATE DATABASE "{name}"'))
        await engine.dispose()

    asyncio.run(_run())


def test_baseline_migration_roundtrip(postgis_url: str) -> None:
    """AC2: upgrade head, downgrade -1, downgrade base, upgrade head on an empty database."""
    base = make_url(postgis_url)
    admin_url = base.set(database="postgres").render_as_string(hide_password=False)
    target_url = base.set(database="migration_roundtrip").render_as_string(hide_password=False)
    _recreate_database(admin_url, "migration_roundtrip")
    config = alembic_config(target_url)

    command.upgrade(config, "head")
    assert _query_scalar(target_url, "SELECT version_num FROM alembic_version") == "0001"
    assert _query_scalar(target_url, "SELECT postgis_version()")

    command.downgrade(config, "-1")
    assert _query_scalar(target_url, "SELECT count(*) FROM alembic_version") == 0

    command.downgrade(config, "base")
    assert _query_scalar(target_url, "SELECT postgis_version()")

    command.upgrade(config, "head")
    assert _query_scalar(target_url, "SELECT version_num FROM alembic_version") == "0001"
    assert _query_scalar(target_url, "SELECT postgis_version()")
