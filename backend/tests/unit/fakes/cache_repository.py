from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime

from geocaching_planner.domain.cache import (
    Cache,
    CacheLog,
    ImportRun,
    UnsetField,
    UserCacheData,
    UserCacheDataUpdate,
)
from geocaching_planner.domain.errors import NotFoundError
from geocaching_planner.services.ports import UpsertResult


class FakeCacheRepository:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock if clock is not None else lambda: datetime.now(UTC)
        self._caches: dict[str, Cache] = {}
        self._hashes: dict[str, str] = {}
        self._user_data: dict[str, UserCacheData] = {}
        self._logs: dict[int, CacheLog] = {}
        self._import_runs: list[ImportRun] = []

    async def upsert_many(self, caches: Sequence[Cache]) -> UpsertResult:
        latest = {cache.gc_code: cache for cache in caches}
        created: list[str] = []
        updated: list[str] = []
        unchanged: list[str] = []
        waypoint_count = 0

        for gc_code, incoming in latest.items():
            waypoint_count += len(incoming.waypoints or ())
            previous_hash = self._hashes.get(gc_code)
            if previous_hash == incoming.source_hash:
                unchanged.append(gc_code)
                continue

            now = self._clock()
            previous = self._caches.get(gc_code)
            created_at: datetime | None
            if previous is None:
                created.append(gc_code)
                created_at = incoming.created_at or now
            else:
                updated.append(gc_code)
                created_at = previous.created_at

            waypoints = (
                previous.waypoints
                if incoming.waypoints is None and previous is not None
                else incoming.waypoints or ()
            )
            self._caches[gc_code] = replace(
                incoming,
                waypoints=waypoints,
                created_at=created_at,
                updated_at=now,
            )
            self._hashes[gc_code] = incoming.source_hash
            for log in incoming.logs:
                self._logs[log.id] = log

        return UpsertResult(
            created=tuple(created),
            updated=tuple(updated),
            unchanged=tuple(unchanged),
            waypoint_count=waypoint_count,
        )

    async def get(self, gc_code: str) -> Cache | None:
        cache = self._caches.get(gc_code)
        if cache is None:
            return None
        logs = tuple(log for log in self._logs.values() if log.cache_gc_code == gc_code)
        return replace(cache, logs=logs)

    async def get_user_data(self, gc_code: str) -> UserCacheData | None:
        return self._user_data.get(gc_code)

    async def set_user_data(self, gc_code: str, update: UserCacheDataUpdate) -> UserCacheData:
        if gc_code not in self._caches:
            raise NotFoundError(f"Cache {gc_code} was not found")
        previous = self._user_data.get(gc_code, UserCacheData(cache_gc_code=gc_code))
        note = previous.note
        corrected_location = previous.corrected_location
        if update.note is not UnsetField.UNSET:
            note = update.note or ""
        if update.corrected_location is not UnsetField.UNSET:
            corrected_location = update.corrected_location
        value = UserCacheData(
            cache_gc_code=gc_code,
            note=note,
            corrected_location=corrected_location,
        )
        self._user_data[gc_code] = value
        return value

    async def add_import_run(self, run: ImportRun) -> ImportRun:
        saved = replace(run, id=len(self._import_runs) + 1)
        self._import_runs.append(saved)
        return saved
