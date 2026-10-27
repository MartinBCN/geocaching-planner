"""Pure cache query filters, paging values, and repository projections."""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from geocaching_planner.domain.cache import CacheType, ContainerSize, Coordinates


@dataclass(frozen=True)
class BoundingBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def __post_init__(self) -> None:
        values = (self.min_lon, self.min_lat, self.max_lon, self.max_lat)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("bbox coordinates must be finite numbers.")
        if not -180 <= self.min_lon <= 180 or not -180 <= self.max_lon <= 180:
            raise ValueError("bbox longitude must be between -180 and 180.")
        if not -90 <= self.min_lat <= 90 or not -90 <= self.max_lat <= 90:
            raise ValueError("bbox latitude must be between -90 and 90.")
        if self.min_lon >= self.max_lon or self.min_lat >= self.max_lat:
            raise ValueError("bbox minimum longitude and latitude must be below their maximum.")


@dataclass(frozen=True)
class CacheFilter:
    types: tuple[CacheType, ...] = ()
    containers: tuple[ContainerSize, ...] = ()
    difficulty_min: float | None = None
    difficulty_max: float | None = None
    terrain_min: float | None = None
    terrain_max: float | None = None
    found: bool | None = None
    include_archived: bool = False
    include_disabled: bool = True
    max_distance_km: float | None = None
    bbox: BoundingBox | None = None
    text: str | None = None
    home_location: Coordinates | None = None

    def __post_init__(self) -> None:
        if not all(isinstance(value, CacheType) for value in self.types):
            raise ValueError("types must be valid cache types.")
        if not all(isinstance(value, ContainerSize) for value in self.containers):
            raise ValueError("containers must be valid container sizes.")
        for name in ("difficulty_min", "difficulty_max", "terrain_min", "terrain_max"):
            value = getattr(self, name)
            if value is not None and (
                not math.isfinite(value) or not 1 <= value <= 5 or value * 2 % 1
            ):
                raise ValueError(f"{name} must be between 1 and 5 in increments of 0.5.")
        if (
            self.difficulty_min is not None
            and self.difficulty_max is not None
            and self.difficulty_min > self.difficulty_max
        ):
            raise ValueError("difficulty_min must not exceed difficulty_max.")
        if (
            self.terrain_min is not None
            and self.terrain_max is not None
            and self.terrain_min > self.terrain_max
        ):
            raise ValueError("terrain_min must not exceed terrain_max.")
        if self.max_distance_km is not None and (
            not math.isfinite(self.max_distance_km) or self.max_distance_km < 0
        ):
            raise ValueError("max_distance_km must be a finite number greater than or equal to 0.")
        if self.text is not None:
            text = self.text.strip()
            object.__setattr__(self, "text", text or None)


class CacheSort(StrEnum):
    NAME = "name"
    NAME_DESC = "-name"
    GC_CODE = "gc_code"
    GC_CODE_DESC = "-gc_code"
    DIFFICULTY = "difficulty"
    DIFFICULTY_DESC = "-difficulty"
    TERRAIN = "terrain"
    TERRAIN_DESC = "-terrain"
    DISTANCE = "distance"
    DISTANCE_DESC = "-distance"
    PLACED_AT = "placed_at"
    PLACED_AT_DESC = "-placed_at"

    @property
    def field(self) -> str:
        return self.value.removeprefix("-")

    @property
    def descending(self) -> bool:
        return self.value.startswith("-")


@dataclass(frozen=True)
class CachePageRequest:
    page: int = 1
    page_size: int = 50

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be at least 1.")
        if not 1 <= self.page_size <= 500:
            raise ValueError("page_size must be between 1 and 500.")


@dataclass(frozen=True)
class CacheSummary:
    gc_code: str
    name: str
    type: CacheType
    container: ContainerSize
    difficulty: float
    terrain: float
    found_by_me: bool
    is_available: bool
    is_archived: bool
    placed_at: datetime | None
    lat: float
    lon: float
    has_corrected: bool
    distance_km: float | None


@dataclass(frozen=True)
class CachePage:
    items: tuple[CacheSummary, ...]
    total: int


@dataclass(frozen=True)
class CacheMarker:
    gc_code: str
    name: str
    lat: float
    lon: float
    type: CacheType
    container: ContainerSize
    difficulty: float
    terrain: float
    found_by_me: bool
    is_available: bool
    is_archived: bool
    has_corrected: bool

    def as_tuple(
        self,
    ) -> tuple[
        str, str, float, float, CacheType, ContainerSize, float, float, bool, bool, bool, bool
    ]:
        return (
            self.gc_code,
            self.name,
            self.lat,
            self.lon,
            self.type,
            self.container,
            self.difficulty,
            self.terrain,
            self.found_by_me,
            self.is_available,
            self.is_archived,
            self.has_corrected,
        )


@dataclass(frozen=True)
class CacheMarkers:
    items: tuple[CacheMarker, ...]
    truncated: bool
    total: int
