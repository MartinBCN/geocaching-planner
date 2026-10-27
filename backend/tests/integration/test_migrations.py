import asyncio

from alembic import command
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from geocaching_planner.adapters.db.migrations import alembic_config

DOMAIN_TABLES = {
    "caches",
    "cache_waypoints",
    "cache_logs",
    "user_cache_data",
    "import_runs",
    "settings",
}


def _schema_snapshot(url: str) -> object:
    return _query_scalar(
        url,
        """
        SELECT jsonb_build_object(
          'columns', (
            SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name, ordinal_position)
            FROM (
              SELECT table_name, column_name, ordinal_position, data_type, udt_name,
                     is_nullable, column_default
              FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name IN
                ('caches', 'cache_waypoints', 'cache_logs', 'user_cache_data', 'import_runs',
                 'settings')
            ) c
          ),
          'indexes', (
            SELECT jsonb_agg(indexdef ORDER BY indexname) FROM pg_indexes
            WHERE schemaname = 'public' AND tablename IN
              ('caches', 'cache_waypoints', 'cache_logs', 'user_cache_data', 'import_runs',
               'settings')
          ),
          'constraints', (
            SELECT jsonb_agg(pg_get_constraintdef(oid) ORDER BY conname)
            FROM pg_constraint
            WHERE conrelid IN ('caches'::regclass, 'cache_waypoints'::regclass,
                              'cache_logs'::regclass, 'user_cache_data'::regclass,
                              'import_runs'::regclass, 'settings'::regclass)
          )
        )
        """,
    )


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
    assert _query_scalar(target_url, "SELECT version_num FROM alembic_version") == "0004"
    assert _query_scalar(target_url, "SELECT postgis_version()")
    snapshot = _schema_snapshot(target_url)

    command.downgrade(config, "-1")
    assert _query_scalar(target_url, "SELECT version_num FROM alembic_version") == "0003"
    assert _query_scalar(target_url, "SELECT to_regclass('public.settings')") == "settings"

    command.upgrade(config, "head")
    assert _schema_snapshot(target_url) == snapshot

    command.downgrade(config, "base")
    assert _query_scalar(target_url, "SELECT count(*) FROM alembic_version") == 0
    for table in DOMAIN_TABLES:
        assert _query_scalar(target_url, f"SELECT to_regclass('public.{table}')") is None
    assert _query_scalar(target_url, "SELECT postgis_version()")

    command.upgrade(config, "head")
    assert _query_scalar(target_url, "SELECT version_num FROM alembic_version") == "0004"
    assert _query_scalar(target_url, "SELECT postgis_version()")
    assert _schema_snapshot(target_url) == snapshot


def test_cache_tables_and_named_indexes_exist(postgis_url: str) -> None:
    async def _run() -> None:
        engine = create_async_engine(postgis_url)
        async with engine.connect() as conn:
            rows = await conn.execute(
                text("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'")
            )
            indexes: dict[str, str] = dict(rows.all())
            assert "USING gist" in indexes["ix_caches_location_gist"]
            assert "USING gist" in indexes["ix_user_cache_data_corrected_location_gist"]
            assert "USING gist" in indexes["ix_caches_location_geometry_gist"]
            assert "USING gist" in indexes["ix_user_cache_data_corrected_geometry_gist"]
            for column in ("type", "difficulty", "terrain", "found_by_me", "is_archived"):
                assert "USING btree" in indexes[f"ix_caches_{column}"]
        await engine.dispose()

    asyncio.run(_run())
