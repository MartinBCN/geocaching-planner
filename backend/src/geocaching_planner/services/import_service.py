"""Synchronous-source, asynchronous-persistence import orchestration."""

import asyncio
from collections.abc import Callable, Iterator, Sequence
from dataclasses import replace
from datetime import UTC, datetime

from geocaching_planner.domain.cache import Cache, ImportIssue, ImportRun
from geocaching_planner.services.ports import (
    CacheParseResult,
    CacheRepository,
    CacheSource,
    ParsedCache,
    ParseError,
    ParseIssue,
    ParseWarning,
    SourceFile,
)

BATCH_SIZE = 500
type SourceFactory = Callable[[Sequence[SourceFile]], CacheSource]


class ImportService:
    """Imports synchronously parsed caches using independent 500-cache transactions."""

    def __init__(self, source_factory: SourceFactory, repo: CacheRepository) -> None:
        self._source_factory = source_factory
        self._repo = repo

    async def import_files(self, files: Sequence[SourceFile]) -> ImportRun:
        started_at = datetime.now(UTC)
        filenames = tuple(source.filename for source in files)
        source = self._source_factory(files)
        errors: list[ImportIssue] = []
        created = updated = unchanged = waypoints = 0
        batch: list[Cache] = []

        async def persist_batch() -> None:
            nonlocal created, updated, unchanged, waypoints
            result = await self._repo.upsert_many(batch)
            created += len(result.created)
            updated += len(result.updated)
            unchanged += len(result.unchanged)
            waypoints += result.waypoint_count
            batch.clear()

        try:
            iterator = iter(source.iter_caches())
            while (result := await asyncio.to_thread(_next_result, iterator)) is not None:
                if isinstance(result, ParseError):
                    errors.append(_as_import_issue(result.issue))
                    continue
                if isinstance(result, ParseWarning):
                    errors.append(_as_import_issue(result.issue))
                    continue
                if not isinstance(result, ParsedCache):
                    continue

                errors.extend(_as_import_issue(issue) for issue in result.warnings)
                batch.append(replace(result.cache, source=source.source_name))
                if len(batch) == BATCH_SIZE:
                    await persist_batch()

            if batch:
                await persist_batch()
        except Exception:
            errors.append(
                ImportIssue(
                    severity="error",
                    file=", ".join(filenames),
                    code="import_failed",
                    message="Import stopped because parsing or persistence failed.",
                )
            )
            await self._repo.add_import_run(
                _make_run(
                    started_at,
                    source.source_name,
                    filenames,
                    created,
                    updated,
                    unchanged,
                    waypoints,
                    errors,
                )
            )
            raise

        return await self._repo.add_import_run(
            _make_run(
                started_at,
                source.source_name,
                filenames,
                created,
                updated,
                unchanged,
                waypoints,
                errors,
            )
        )


def _next_result(iterator: Iterator[CacheParseResult]) -> CacheParseResult | None:
    return next(iterator, None)


def _as_import_issue(issue: ParseIssue) -> ImportIssue:
    return ImportIssue(
        severity=issue.severity,
        file=issue.file,
        gc_code=issue.gc_code,
        line=issue.line,
        code=issue.code,
        message=issue.message,
    )


def _make_run(
    started_at: datetime,
    source: str,
    filenames: tuple[str, ...],
    created: int,
    updated: int,
    unchanged: int,
    waypoints: int,
    errors: Sequence[ImportIssue],
) -> ImportRun:
    return ImportRun(
        started_at=started_at,
        finished_at=datetime.now(UTC),
        source=source,
        filenames=filenames,
        created=created,
        updated=updated,
        unchanged=unchanged,
        waypoints=waypoints,
        errors=tuple(errors),
    )
