"""Protocols and result types shared by application services and adapters."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import BinaryIO, Literal, Protocol

from geocaching_planner.domain.cache import Cache, ImportRun, UserCacheData, UserCacheDataUpdate
from geocaching_planner.domain.settings import PlannerSettings


@dataclass(frozen=True, kw_only=True)
class UpsertResult:
    created: tuple[str, ...]
    updated: tuple[str, ...]
    unchanged: tuple[str, ...]
    waypoint_count: int


class CacheRepository(Protocol):
    async def upsert_many(self, caches: Sequence[Cache]) -> UpsertResult: ...

    async def get(self, gc_code: str) -> Cache | None: ...

    async def get_user_data(self, gc_code: str) -> UserCacheData | None: ...

    async def set_user_data(self, gc_code: str, update: UserCacheDataUpdate) -> UserCacheData: ...

    async def add_import_run(self, run: ImportRun) -> ImportRun: ...

    async def list_import_runs(self) -> Sequence[ImportRun]: ...


@dataclass(frozen=True)
class SourceFile:
    filename: str
    stream: BinaryIO


@dataclass(frozen=True, kw_only=True)
class ParseIssue:
    severity: Literal["warning", "error"]
    file: str
    gc_code: str | None
    line: int | None
    code: str
    message: str


@dataclass(frozen=True, kw_only=True)
class ParsedCache:
    cache: Cache
    warnings: tuple[ParseIssue, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ParseError:
    issue: ParseIssue


@dataclass(frozen=True, kw_only=True)
class ParseWarning:
    issue: ParseIssue


CacheParseResult = ParsedCache | ParseError | ParseWarning


class CacheSource(Protocol):
    source_name: str

    def iter_caches(self) -> Iterator[CacheParseResult]: ...


class SettingsRepository(Protocol):
    async def get(self) -> PlannerSettings | None: ...

    async def save(self, settings: PlannerSettings) -> PlannerSettings: ...
