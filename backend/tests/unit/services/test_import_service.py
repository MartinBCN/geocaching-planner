import io
from collections.abc import Iterator, Sequence
from threading import get_ident

import pytest

from geocaching_planner.domain.cache import (
    Cache,
    CacheType,
    ContainerSize,
    Coordinates,
)
from geocaching_planner.services.import_service import ImportService
from geocaching_planner.services.ports import (
    CacheParseResult,
    ParsedCache,
    ParseError,
    ParseIssue,
    ParseWarning,
    SourceFile,
    UpsertResult,
)
from tests.unit.fakes.cache_repository import FakeCacheRepository


class SyntheticSource:
    source_name = "synthetic"

    def __init__(self, results: Sequence[CacheParseResult]) -> None:
        self.results = results

    def iter_caches(self) -> Iterator[CacheParseResult]:
        yield from self.results


class RecordingRepository(FakeCacheRepository):
    def __init__(self, *, fail_on_call: int | None = None) -> None:
        super().__init__()
        self.batch_sizes: list[int] = []
        self.fail_on_call = fail_on_call

    async def upsert_many(self, caches: Sequence[Cache]) -> UpsertResult:
        self.batch_sizes.append(len(caches))
        if self.fail_on_call == len(self.batch_sizes):
            raise RuntimeError("synthetic persistence failure")
        return await super().upsert_many(caches)


def _cache(index: int) -> Cache:
    return Cache(
        gc_code=f"GC{index:06d}",
        name=f"Synthetic {index}",
        type=CacheType.TRADITIONAL,
        container=ContainerSize.SMALL,
        difficulty=1.5,
        terrain=2,
        owner="Synthetic owner",
        location=Coordinates(52.1, 4.3),
    )


def _parsed(index: int) -> ParsedCache:
    return ParsedCache(cache=_cache(index))


async def test_imports_caches_in_batches_of_500_and_records_history() -> None:
    repository = RecordingRepository()
    files = [SourceFile("synthetic.gpx", io.BytesIO(b""))]
    service = ImportService(
        lambda _files: SyntheticSource([_parsed(index) for index in range(1200)]),
        repository,
    )

    run = await service.import_files(files)

    assert repository.batch_sizes == [500, 500, 200]
    assert (run.created, run.updated, run.unchanged, run.waypoints) == (1200, 0, 0, 0)
    assert run.source == "synthetic"
    assert run.filenames == ("synthetic.gpx",)
    assert run.finished_at is not None
    assert run.started_at <= run.finished_at
    assert (await repository.list_import_runs()) == (run,)


async def test_partial_counts_and_error_are_recorded_after_batch_failure() -> None:
    repository = RecordingRepository(fail_on_call=2)
    service = ImportService(
        lambda _files: SyntheticSource([_parsed(index) for index in range(700)]),
        repository,
    )

    with pytest.raises(RuntimeError, match="synthetic persistence failure"):
        await service.import_files([])

    (run,) = await repository.list_import_runs()
    assert run.created == 500
    assert run.updated == run.unchanged == 0
    assert len(run.errors) == 1
    assert run.errors[0].code == "import_failed"


async def test_parser_errors_and_warnings_are_saved_with_context() -> None:
    issue = ParseIssue(
        severity="error",
        file="broken.gpx",
        gc_code="GC000002",
        line=12,
        code="invalid_entry",
        message="Entry is malformed.",
    )
    warning = ParseIssue(
        severity="warning",
        file="waypoints.gpx",
        gc_code="GC000003",
        line=None,
        code="orphan_waypoint",
        message="Waypoint has no cache.",
    )
    repository = RecordingRepository()
    service = ImportService(
        lambda _files: SyntheticSource(
            [
                ParsedCache(cache=_cache(1), warnings=(warning,)),
                ParseError(issue=issue),
                ParseWarning(issue=warning),
            ]
        ),
        repository,
    )

    run = await service.import_files([])

    assert run.created == 1
    assert [(item.severity, item.code) for item in run.errors] == [
        ("warning", "orphan_waypoint"),
        ("error", "invalid_entry"),
        ("warning", "orphan_waypoint"),
    ]
    assert run.errors[1].gc_code == "GC000002"
    assert run.errors[1].line == 12


async def test_synchronous_parser_runs_off_the_event_loop() -> None:
    parser_thread: list[int] = []
    repository = RecordingRepository()

    class ThreadRecordingSource(SyntheticSource):
        def iter_caches(self) -> Iterator[CacheParseResult]:
            parser_thread.append(get_ident())
            yield _parsed(1)

    await ImportService(
        lambda _files: ThreadRecordingSource([]),
        repository,
    ).import_files([])

    assert parser_thread
    assert parser_thread[0] != get_ident()
