import asyncio
import io
import zipfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.cache_repository import SqlAlchemyCacheRepository
from geocaching_planner.adapters.db.models import (
    CacheLogModel,
    CacheModel,
    CacheWaypointModel,
    ImportRunModel,
)
from geocaching_planner.adapters.gpx import upload_validation
from geocaching_planner.api.deps import get_session
from geocaching_planner.api.routes import imports as import_routes
from geocaching_planner.config import AppConfig
from geocaching_planner.domain.cache import Coordinates, UserCacheDataUpdate
from geocaching_planner.main import create_app
from tests.conftest import FakeProbe
from tests.fixtures.pq.import_fixture import make_import_fixture

FIXTURES = Path(__file__).parents[2] / "fixtures" / "pq"


@asynccontextmanager
async def _client(config: AppConfig, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(config, database_probe=FakeProbe())

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_import_upload_upserts_and_history_is_newest_first(
    config: AppConfig, db_session: AsyncSession
) -> None:
    gpx, waypoints = make_import_fixture()
    async with _client(config, db_session) as client:
        first = await client.post(
            "/api/v1/imports",
            files=[
                ("files", ("pocket-query.gpx", gpx, "application/gpx+xml")),
                ("files", ("pocket-query-wpts.gpx", waypoints, "application/gpx+xml")),
            ],
        )
        updated_at_first = await db_session.scalar(
            select(CacheModel.updated_at).where(CacheModel.gc_code == "GC1001A")
        )
        second = await client.post(
            "/api/v1/imports",
            files=[
                ("files", ("pocket-query.gpx", gpx, "application/gpx+xml")),
                ("files", ("pocket-query-wpts.gpx", waypoints, "application/gpx+xml")),
            ],
        )
        updated_at_second = await db_session.scalar(
            select(CacheModel.updated_at).where(CacheModel.gc_code == "GC1001A")
        )
        history = await client.get("/api/v1/imports")

    assert first.status_code == second.status_code == 201
    assert first.json()["created"] == 3
    assert first.json()["waypoints"] == 2
    assert first.json()["filenames"] == ["pocket-query.gpx", "pocket-query-wpts.gpx"]
    assert first.json()["started_at"] is not None
    assert second.json()["unchanged"] == 3
    assert updated_at_first == updated_at_second
    assert history.status_code == 200
    assert [run["id"] for run in history.json()] == [
        second.json()["id"],
        first.json()["id"],
    ]
    assert await db_session.scalar(select(func.count()).select_from(CacheModel)) == 3
    assert await db_session.scalar(select(func.count()).select_from(CacheWaypointModel)) == 2
    log_count = await db_session.scalar(select(func.count()).select_from(CacheLogModel))
    assert log_count == 2


async def test_source_update_preserves_note_and_corrected_location(
    config: AppConfig, db_session: AsyncSession
) -> None:
    gpx, waypoints = make_import_fixture()
    repository = SqlAlchemyCacheRepository(db_session)
    async with _client(config, db_session) as client:
        first = await client.post(
            "/api/v1/imports",
            files=[
                ("files", ("pocket-query.gpx", gpx, "application/gpx+xml")),
                ("files", ("pocket-query-wpts.gpx", waypoints, "application/gpx+xml")),
            ],
        )
        await repository.set_user_data(
            "GC1002B",
            UserCacheDataUpdate(
                note="Keep my note",
                corrected_location=Coordinates(53.2, 5.4),
            ),
        )
        updated_gpx = gpx.replace(b"Synthetic cache 2", b"Updated synthetic cache")
        updated = await client.post(
            "/api/v1/imports",
            files=[
                ("files", ("pocket-query.gpx", updated_gpx, "application/gpx+xml")),
                ("files", ("pocket-query-wpts.gpx", waypoints, "application/gpx+xml")),
            ],
        )

    assert first.status_code == updated.status_code == 201
    assert updated.json()["updated"] == 1
    user_data = await repository.get_user_data("GC1002B")
    assert user_data is not None
    assert user_data.note == "Keep my note"
    assert user_data.corrected_location == Coordinates(53.2, 5.4)


async def test_corrupt_entry_returns_partial_success(
    config: AppConfig, db_session: AsyncSession
) -> None:
    content = (FIXTURES / "three_caches_one_corrupt_entry.gpx").read_bytes()
    async with _client(config, db_session) as client:
        response = await client.post(
            "/api/v1/imports",
            files=[("files", ("partial.gpx", content, "application/gpx+xml"))],
        )

    result = response.json()
    assert response.status_code == 201
    assert result["created"] == 2
    assert len([issue for issue in result["errors"] if issue["severity"] == "error"]) == 1
    assert await db_session.scalar(select(func.count()).select_from(CacheModel)) == 2


async def test_prevalidation_rejects_all_files_before_import(
    config: AppConfig, db_session: AsyncSession
) -> None:
    valid = (FIXTURES / "cache.gpx").read_bytes()
    async with _client(config, db_session) as client:
        response = await client.post(
            "/api/v1/imports",
            files=[
                ("files", ("valid.gpx", valid, "application/gpx+xml")),
                ("files", ("unsupported.txt", b"not GPX", "text/plain")),
            ],
        )

    assert response.status_code == 415
    assert response.headers["content-type"].startswith("application/problem+json")
    assert await db_session.scalar(select(func.count()).select_from(CacheModel)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ImportRunModel)) == 0


async def test_invalid_gpx_content_rejects_mixed_request(
    config: AppConfig, db_session: AsyncSession
) -> None:
    valid = (FIXTURES / "cache.gpx").read_bytes()
    async with _client(config, db_session) as client:
        response = await client.post(
            "/api/v1/imports",
            files=[
                ("files", ("valid.gpx", valid, "application/gpx+xml")),
                ("files", ("invalid.gpx", b"not an XML or GPX document", "application/gpx+xml")),
            ],
        )

    assert response.status_code == 415
    assert response.headers["content-type"].startswith("application/problem+json")
    assert await db_session.scalar(select(func.count()).select_from(CacheModel)) == 0


async def test_zip_upload_and_waypoint_only_upload(
    config: AppConfig, db_session: AsyncSession
) -> None:
    gpx, waypoints = make_import_fixture()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("pocket-query.gpx", gpx)
        zipped.writestr("pocket-query-wpts.gpx", waypoints)

    async with _client(config, db_session) as client:
        imported = await client.post(
            "/api/v1/imports",
            files=[("files", ("pocket-query.zip", archive.getvalue(), "application/zip"))],
        )
        waypoint_only = await client.post(
            "/api/v1/imports",
            files=[("files", ("orphan-wpts.gpx", waypoints, "application/gpx+xml"))],
        )

    assert imported.status_code == 201
    assert imported.json()["created"] == 3
    assert imported.json()["waypoints"] == 2
    warnings = [issue for issue in waypoint_only.json()["errors"] if issue["severity"] == "warning"]
    assert waypoint_only.status_code == 201
    assert waypoint_only.json()["created"] == 0
    assert len(warnings) == 2
    assert all(issue["code"] == "orphan_waypoint" for issue in warnings)


async def test_temporary_directory_is_removed_after_success_and_failure(
    config: AppConfig,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_temporary_directory = TemporaryDirectory
    temporary_directories: list[TemporaryDirectory[str]] = []

    def create_temporary_directory(*, prefix: str) -> TemporaryDirectory[str]:
        directory = original_temporary_directory(prefix=prefix)
        temporary_directories.append(directory)
        return directory

    monkeypatch.setattr(import_routes, "TemporaryDirectory", create_temporary_directory)
    gpx = (FIXTURES / "cache.gpx").read_bytes()
    async with _client(config, db_session) as client:
        success = await client.post(
            "/api/v1/imports",
            files=[("files", ("success.gpx", gpx, "application/gpx+xml"))],
        )
        failure = await client.post(
            "/api/v1/imports",
            files=[("files", ("bad.txt", b"invalid", "text/plain"))],
        )

    assert success.status_code == 201
    assert failure.status_code == 415
    assert len(temporary_directories) == 2
    for directory in temporary_directories:
        assert not await asyncio.to_thread(Path(directory.name).exists)


async def test_file_size_limit_returns_problem_without_import(
    db_session: AsyncSession,
) -> None:
    config = AppConfig(_env_file=None, import_max_file_mb=1)
    content = b"<gpx " + b" " * (1024 * 1024) + b"/>"
    async with _client(config, db_session) as client:
        response = await client.post(
            "/api/v1/imports",
            files=[("files", ("too-large.gpx", content, "application/gpx+xml"))],
        )

    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")
    assert await db_session.scalar(select(func.count()).select_from(CacheModel)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ImportRunModel)) == 0


async def test_expanded_archive_limit_returns_413_before_import(
    config: AppConfig,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gpx = (FIXTURES / "cache.gpx").read_bytes()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("pocket-query.gpx", gpx)
    monkeypatch.setattr(upload_validation, "MAX_EXPANDED_SIZE", 32)
    async with _client(config, db_session) as client:
        response = await client.post(
            "/api/v1/imports",
            files=[("files", ("pocket-query.zip", archive.getvalue(), "application/zip"))],
        )

    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")
    assert await db_session.scalar(select(func.count()).select_from(CacheModel)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ImportRunModel)) == 0


async def test_import_history_is_empty_on_fresh_database(
    config: AppConfig, db_session: AsyncSession
) -> None:
    async with _client(config, db_session) as client:
        response = await client.get("/api/v1/imports")

    assert response.status_code == 200
    assert response.json() == []
