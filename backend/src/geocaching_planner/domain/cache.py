"""Imported cache aggregates, kept separate from user-owned data."""

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal


class CacheType(StrEnum):
    TRADITIONAL = "Traditional"
    MULTI = "Multi"
    MYSTERY = "Mystery"
    LETTERBOX = "Letterbox"
    EARTHCACHE = "EarthCache"
    WHERIGO = "Wherigo"
    VIRTUAL = "Virtual"
    EVENT = "Event"
    CITO = "CITO"
    MEGA = "Mega"
    GIGA = "Giga"
    WEBCAM = "Webcam"
    LAB = "Lab"
    OTHER = "Other"


class ContainerSize(StrEnum):
    MICRO = "Micro"
    SMALL = "Small"
    REGULAR = "Regular"
    LARGE = "Large"
    VIRTUAL = "Virtual"
    OTHER = "Other"
    NOT_CHOSEN = "Not chosen"


class WaypointType(StrEnum):
    PARKING_AREA = "Parking Area"
    STAGE_OF_A_MULTICACHE = "Stage of a Multicache"
    STAGES_OF_A_MULTICACHE = "Stages of a Multicache"
    QUESTION_TO_ANSWER = "Question to Answer"
    FINAL_LOCATION = "Final Location"
    TRAILHEAD = "Trailhead"
    REFERENCE_POINT = "Reference Point"
    OTHER = "Other"


class LogType(StrEnum):
    FOUND_IT = "Found it"
    DID_NOT_FIND_IT = "Didn't find it"
    WRITE_NOTE = "Write note"
    NEEDS_ARCHIVED = "Needs Archived"
    NEEDS_MAINTENANCE = "Needs Maintenance"
    OWNER_MAINTENANCE = "Owner Maintenance"
    WILL_ATTEND = "Will Attend"
    ATTENDED = "Attended"
    WEBCAM_PHOTO_TAKEN = "Webcam Photo Taken"
    TEMPORARILY_DISABLE_LISTING = "Temporarily Disable Listing"
    ENABLE_LISTING = "Enable Listing"
    PUBLISH_LISTING = "Publish Listing"
    RETRACT_LISTING = "Retract Listing"
    UPDATE_COORDINATES = "Update Coordinates"
    ANNOUNCEMENT = "Announcement"
    ARCHIVE = "Archive"
    UNARCHIVE = "Unarchive"
    OTHER = "Other"


@dataclass(frozen=True)
class Coordinates:
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.lat) or not -90 <= self.lat <= 90:
            raise ValueError("Latitude must be finite and between -90 and 90")
        if not math.isfinite(self.lon) or not -180 <= self.lon <= 180:
            raise ValueError("Longitude must be finite and between -180 and 180")
        object.__setattr__(self, "lat", float(self.lat) if self.lat else 0.0)
        object.__setattr__(self, "lon", float(self.lon) if self.lon else 0.0)


@dataclass(frozen=True)
class CacheAttribute:
    id: int
    included: bool
    text: str = ""


@dataclass(frozen=True, kw_only=True)
class CacheWaypoint:
    cache_gc_code: str
    code: str
    name: str
    type: WaypointType
    source_type: str
    prefix: str = ""
    location: Coordinates | None = None
    description: str = ""
    id: int | None = None


@dataclass(frozen=True, kw_only=True)
class CacheLog:
    id: int
    cache_gc_code: str
    type: LogType
    source_type: str
    finder: str
    logged_at: datetime
    text: str = ""


@dataclass(frozen=True, kw_only=True)
class Cache:
    gc_code: str
    name: str
    type: CacheType
    container: ContainerSize
    difficulty: float
    terrain: float
    owner: str
    location: Coordinates
    source_type: str = ""
    source_container: str = ""
    placed_at: datetime | None = None
    country: str = ""
    state: str = ""
    short_description: str = ""
    long_description: str = ""
    description_is_html: bool = False
    hint: str = ""
    attributes: tuple[CacheAttribute, ...] = ()
    is_available: bool = True
    is_archived: bool = False
    found_by_me: bool = False
    found_at: datetime | None = None
    source: str = "pq"
    source_updated_at: datetime | None = None
    waypoints: tuple[CacheWaypoint, ...] | None = None
    logs: tuple[CacheLog, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("difficulty", "terrain"):
            value = getattr(self, name)
            if not math.isfinite(value) or not 1 <= value <= 5 or value * 2 % 1:
                raise ValueError(f"{name} must be between 1 and 5 in steps of 0.5")
            object.__setattr__(self, name, float(value))

    @property
    def source_hash(self) -> str:
        return content_hash(self)


@dataclass(frozen=True, kw_only=True)
class UserCacheData:
    cache_gc_code: str
    note: str = ""
    corrected_location: Coordinates | None = None


@dataclass(frozen=True, kw_only=True)
class ImportIssue:
    severity: Literal["warning", "error"]
    file: str
    code: str
    message: str
    gc_code: str | None = None
    line: int | None = None


@dataclass(frozen=True, kw_only=True)
class ImportRun:
    started_at: datetime
    source: str
    filenames: tuple[str, ...]
    id: int | None = None
    finished_at: datetime | None = None
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    waypoints: int = 0
    errors: tuple[ImportIssue, ...] = ()


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat() if value.tzinfo else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Cannot hash source value of type {type(value).__name__}")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        default=_json_default,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def content_hash(cache: Cache) -> str:
    """Hash source content, not persistence metadata or collection ordering."""
    source = asdict(cache)
    del source["created_at"], source["updated_at"]
    if source["waypoints"] is not None:
        for waypoint in source["waypoints"]:
            del waypoint["id"]
    for collection in ("attributes", "waypoints", "logs"):
        if source[collection] is not None:
            source[collection] = sorted(source[collection], key=_canonical_json)
    return hashlib.sha256(_canonical_json(source).encode("utf-8")).hexdigest()
