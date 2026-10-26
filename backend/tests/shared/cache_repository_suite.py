from datetime import UTC, datetime

from geocaching_planner.domain.cache import (
    Cache,
    CacheLog,
    CacheType,
    CacheWaypoint,
    ContainerSize,
    Coordinates,
    ImportIssue,
    ImportRun,
    LogType,
    UserCacheDataUpdate,
    WaypointType,
)
from geocaching_planner.services.ports import CacheRepository


def make_cache(
    gc_code: str,
    *,
    name: str | None = None,
    waypoints: tuple[CacheWaypoint, ...] | None = (),
    logs: tuple[CacheLog, ...] = (),
) -> Cache:
    return Cache(
        gc_code=gc_code,
        name=name or f"Cache {gc_code}",
        type=CacheType.TRADITIONAL,
        container=ContainerSize.REGULAR,
        difficulty=2.0,
        terrain=2.5,
        owner="Synthetic owner",
        location=Coordinates(lat=52.1, lon=4.3),
        waypoints=waypoints,
        logs=logs,
    )


def make_waypoint(gc_code: str, code: str, *, name: str | None = None) -> CacheWaypoint:
    return CacheWaypoint(
        cache_gc_code=gc_code,
        code=code,
        name=name or f"Waypoint {code}",
        type=WaypointType.PARKING_AREA,
        source_type="Parking Area",
        location=Coordinates(lat=52.2, lon=4.4),
    )


def make_log(
    gc_code: str,
    log_id: int,
    *,
    text: str = "Synthetic log",
    finder: str = "Synthetic finder",
) -> CacheLog:
    return CacheLog(
        id=log_id,
        cache_gc_code=gc_code,
        type=LogType.FOUND_IT,
        source_type="Found it",
        finder=finder,
        logged_at=datetime(2025, 1, 1, tzinfo=UTC),
        text=text,
    )


async def verify_create_update_and_noop(repository: CacheRepository) -> None:
    original = make_cache("GC-SHARED-AC1")
    first = await repository.upsert_many([original])
    stored = await repository.get(original.gc_code)
    assert first.created == (original.gc_code,)
    assert first.updated == ()
    assert first.unchanged == ()
    assert stored is not None
    assert stored.created_at is not None
    assert stored.updated_at is not None
    created_at, updated_at = stored.created_at, stored.updated_at

    same = await repository.upsert_many([original])
    unchanged = await repository.get(original.gc_code)
    assert same.unchanged == (original.gc_code,)
    assert unchanged is not None
    assert unchanged.created_at == created_at
    assert unchanged.updated_at == updated_at

    changed = await repository.upsert_many([make_cache(original.gc_code, name="Updated")])
    updated = await repository.get(original.gc_code)
    assert changed.updated == (original.gc_code,)
    assert updated is not None
    assert updated.name == "Updated"
    assert updated.created_at == created_at
    assert updated.updated_at is not None
    assert updated.updated_at > updated_at


async def verify_duplicate_codes_last_wins(repository: CacheRepository) -> None:
    first = make_cache("GC-SHARED-AC2", name="First")
    last = make_cache("GC-SHARED-AC2", name="Last")
    result = await repository.upsert_many([first, last])
    stored = await repository.get(first.gc_code)
    assert result.created == (first.gc_code,)
    assert stored is not None
    assert stored.name == "Last"


async def verify_logs_upsert_by_source_id(repository: CacheRepository) -> None:
    code = "GC-SHARED-AC3"
    await repository.upsert_many([make_cache(code, logs=(make_log(code, 3001),))])
    await repository.upsert_many(
        [
            make_cache(
                code,
                logs=(
                    make_log(code, 3001, text="Updated log"),
                    make_log(code, 3002),
                ),
            )
        ]
    )
    stored = await repository.get(code)
    assert stored is not None
    assert len(stored.logs) == 2
    by_id = {log.id: log for log in stored.logs}
    assert by_id[3001].text == "Updated log"
    assert by_id[3002].text == "Synthetic log"


async def verify_waypoint_replacement(repository: CacheRepository) -> None:
    code = "GC-SHARED-AC4"
    first = make_waypoint(code, "A1")
    replacement = make_waypoint(code, "A2")
    await repository.upsert_many([make_cache(code, waypoints=(first,))])
    kept = await repository.upsert_many(
        [make_cache(code, name="No waypoint input", waypoints=None)]
    )
    stored = await repository.get(code)
    assert kept.updated == (code,)
    assert stored is not None
    assert [item.code for item in stored.waypoints or ()] == ["A1"]

    await repository.upsert_many([make_cache(code, waypoints=(replacement,))])
    stored = await repository.get(code)
    assert stored is not None
    assert [item.code for item in stored.waypoints or ()] == ["A2"]

    result = await repository.upsert_many([make_cache(code, waypoints=())])
    stored = await repository.get(code)
    assert result.waypoint_count == 0
    assert stored is not None
    assert stored.waypoints == ()


async def verify_user_data_is_preserved_and_partially_updated(
    repository: CacheRepository,
) -> None:
    code = "GC-SHARED-AC5"
    await repository.upsert_many([make_cache(code)])
    corrected = Coordinates(lat=53.0, lon=5.0)
    await repository.set_user_data(
        code, UserCacheDataUpdate(note="Personal note", corrected_location=corrected)
    )

    await repository.upsert_many([make_cache(code, name="Imported update")])
    user_data = await repository.get_user_data(code)
    assert user_data is not None
    assert user_data.note == "Personal note"
    assert user_data.corrected_location == corrected

    note_only = await repository.set_user_data(code, UserCacheDataUpdate(note="Updated note"))
    assert note_only.note == "Updated note"
    assert note_only.corrected_location == corrected

    updated_coordinates = Coordinates(lat=54.0, lon=6.0)
    coordinates_only = await repository.set_user_data(
        code, UserCacheDataUpdate(corrected_location=updated_coordinates)
    )
    assert coordinates_only.note == "Updated note"
    assert coordinates_only.corrected_location == updated_coordinates

    clear_note = await repository.set_user_data(code, UserCacheDataUpdate(note=None))
    assert clear_note.note == ""
    assert clear_note.corrected_location == updated_coordinates
    clear_coordinates = await repository.set_user_data(
        code, UserCacheDataUpdate(corrected_location=None)
    )
    assert clear_coordinates.note == ""
    assert clear_coordinates.corrected_location is None

    stored_cache = await repository.get(code)
    assert stored_cache is not None
    assert stored_cache.location == Coordinates(lat=52.1, lon=4.3)


async def verify_import_run_round_trip(repository: CacheRepository) -> None:
    run = ImportRun(
        started_at=datetime(2025, 1, 1, tzinfo=UTC),
        finished_at=datetime(2025, 1, 1, 0, 1, tzinfo=UTC),
        source="pq",
        filenames=("synthetic.gpx",),
        created=3,
        updated=1,
        unchanged=2,
        waypoints=1,
        errors=(
            ImportIssue(
                severity="warning",
                file="synthetic.gpx",
                gc_code="GC-SHARED",
                line=12,
                code="unmatched-waypoint",
                message="Waypoint has no cache parent.",
            ),
        ),
    )
    saved = await repository.add_import_run(run)
    assert saved.id is not None
    assert saved.source == run.source
    assert saved.filenames == run.filenames
    assert saved.errors == run.errors


async def run_shared_behavior_suite(repository: CacheRepository) -> None:
    await verify_create_update_and_noop(repository)
    await verify_duplicate_codes_last_wins(repository)
    await verify_logs_upsert_by_source_id(repository)
    await verify_waypoint_replacement(repository)
    await verify_user_data_is_preserved_and_partially_updated(repository)
    await verify_import_run_round_trip(repository)
