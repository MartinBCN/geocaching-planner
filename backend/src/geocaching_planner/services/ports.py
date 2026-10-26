"""Protocols and result types shared by application services and adapters."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol

from geocaching_planner.domain.cache import Cache
from geocaching_planner.domain.settings import PlannerSettings


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
