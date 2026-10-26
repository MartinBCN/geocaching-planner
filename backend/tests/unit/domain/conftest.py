from datetime import UTC, datetime

import pytest

from geocaching_planner.domain.cache import (
    Cache,
    CacheAttribute,
    CacheLog,
    CacheType,
    CacheWaypoint,
    ContainerSize,
    Coordinates,
    LogType,
    WaypointType,
)


@pytest.fixture
def cache() -> Cache:
    return Cache(
        gc_code="GC0001A",
        name="Synthetic bicycle cache",
        type=CacheType.TRADITIONAL,
        source_type="Traditional Cache",
        container=ContainerSize.SMALL,
        source_container="Small",
        difficulty=1.5,
        terrain=2,
        owner="Synthetic owner",
        location=Coordinates(52.1, 4.3),
        attributes=(CacheAttribute(1, True, "Bicycles"), CacheAttribute(2, False, "Dogs")),
        waypoints=(
            CacheWaypoint(
                cache_gc_code="GC0001A",
                code="PK0001A",
                name="Parking",
                type=WaypointType.PARKING_AREA,
                source_type="Parking Area",
                location=Coordinates(52.2, 4.4),
            ),
            CacheWaypoint(
                cache_gc_code="GC0001A",
                code="RP0001A",
                name="Reference",
                type=WaypointType.REFERENCE_POINT,
                source_type="Reference Point",
            ),
        ),
        logs=(
            CacheLog(
                id=1,
                cache_gc_code="GC0001A",
                type=LogType.FOUND_IT,
                source_type="Found it",
                finder="Cyclist A",
                logged_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
            CacheLog(
                id=2,
                cache_gc_code="GC0001A",
                type=LogType.WRITE_NOTE,
                source_type="Write note",
                finder="Cyclist B",
                logged_at=datetime(2026, 1, 2, tzinfo=UTC),
            ),
        ),
    )
