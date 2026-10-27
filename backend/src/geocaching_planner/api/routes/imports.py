"""Pocket Query upload and import-history endpoints."""

import asyncio
from collections.abc import Sequence
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Annotated, Literal

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from geocaching_planner.adapters.db.cache_repository import SqlAlchemyCacheRepository
from geocaching_planner.adapters.gpx.pq_source import PocketQuerySource
from geocaching_planner.adapters.gpx.upload_validation import (
    UnsupportedInputError,
    UploadTooLargeError,
    validate_uploads,
)
from geocaching_planner.api.deps import SessionDep, SettingsDep
from geocaching_planner.domain.cache import ImportIssue, ImportRun
from geocaching_planner.services.import_service import ImportService
from geocaching_planner.services.ports import SourceFile

router = APIRouter(tags=["imports"])
_CHUNK_SIZE = 1024 * 1024


class ImportIssueResponse(BaseModel):
    severity: Literal["warning", "error"]
    file: str
    gc_code: str | None
    line: int | None
    code: str
    message: str


class ImportRunResponse(BaseModel):
    id: int | None
    started_at: datetime
    finished_at: datetime | None
    source: str
    filenames: list[str]
    created: int
    updated: int
    unchanged: int
    waypoints: int
    errors: list[ImportIssueResponse]


@router.post("/imports", response_model=ImportRunResponse, status_code=201)
async def import_files(
    session: SessionDep,
    config: SettingsDep,
    files: Annotated[list[UploadFile], File()],
) -> ImportRunResponse:
    max_file_size = config.import_max_file_mb * 1024 * 1024
    with TemporaryDirectory(prefix="geocaching-import-") as directory:
        staged = await _stage_uploads(files, Path(directory), max_file_size)
        try:
            await asyncio.to_thread(validate_uploads, staged)
        except UnsupportedInputError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except UploadTooLargeError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc

        with ExitStack() as stack:
            source_files = [
                SourceFile(filename=filename, stream=stack.enter_context(path.open("rb")))
                for filename, path in staged
            ]
            result = await ImportService(
                PocketQuerySource, SqlAlchemyCacheRepository(session)
            ).import_files(source_files)

    return _response(result)


@router.get("/imports", response_model=list[ImportRunResponse])
async def list_imports(session: SessionDep) -> list[ImportRunResponse]:
    runs = await SqlAlchemyCacheRepository(session).list_import_runs()
    return [_response(run) for run in runs]


async def _stage_uploads(
    uploads: Sequence[UploadFile], directory: Path, max_file_size: int
) -> list[tuple[str, Path]]:
    staged: list[tuple[str, Path]] = []
    for index, upload in enumerate(uploads):
        filename = upload.filename
        if filename is None or PurePosixPath(filename).suffix.casefold() not in {".gpx", ".zip"}:
            raise HTTPException(
                status_code=415,
                detail="Only .gpx and .zip files are supported.",
            )
        suffix = PurePosixPath(filename).suffix.casefold()
        destination = directory / f"upload-{index}{suffix}"
        size = 0
        with destination.open("wb") as output:
            while chunk := await upload.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > max_file_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"{filename} exceeds the {max_file_size // (1024 * 1024)} MB limit.",
                    )
                output.write(chunk)
        staged.append((filename, destination))
    return staged


def _response(run: ImportRun) -> ImportRunResponse:
    return ImportRunResponse(
        id=run.id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        source=run.source,
        filenames=list(run.filenames),
        created=run.created,
        updated=run.updated,
        unchanged=run.unchanged,
        waypoints=run.waypoints,
        errors=[_issue_response(issue) for issue in run.errors],
    )


def _issue_response(issue: ImportIssue) -> ImportIssueResponse:
    return ImportIssueResponse(
        severity=issue.severity,
        file=issue.file,
        gc_code=issue.gc_code,
        line=issue.line,
        code=issue.code,
        message=issue.message,
    )
