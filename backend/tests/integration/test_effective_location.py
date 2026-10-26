from dataclasses import asdict
from datetime import UTC, datetime

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.models import (
    CacheLogModel,
    CacheModel,
    CacheWaypointModel,
    ImportRunModel,
    UserCacheDataModel,
)
from geocaching_planner.adapters.db.spatial import (
    coordinates_to_point,
    effective_location,
    point_to_coordinates,
)
from geocaching_planner.domain.cache import (
    Cache,
    CacheType,
    ContainerSize,
    Coordinates,
    ImportIssue,
    LogType,
    WaypointType,
)


def _cache_model(gc_code: str = "GC0001A") -> CacheModel:
    cache = Cache(
        gc_code=gc_code,
        name="Synthetic cache",
        type=CacheType.TRADITIONAL,
        container=ContainerSize.SMALL,
        difficulty=1.5,
        terrain=2,
        owner="Synthetic owner",
        location=Coordinates(52.1, 4.3),
    )
    return CacheModel(
        gc_code=cache.gc_code,
        name=cache.name,
        type=cache.type,
        container=cache.container,
        difficulty=cache.difficulty,
        terrain=cache.terrain,
        owner=cache.owner,
        source=cache.source,
        source_hash=cache.source_hash,
        location=coordinates_to_point(cache.location),
    )


async def test_coordinates_round_trip(db_session: AsyncSession) -> None:
    db_session.add(_cache_model())
    await db_session.flush()
    db_session.expire_all()
    cache = (await db_session.scalars(select(CacheModel))).one()
    assert point_to_coordinates(cache.location) == Coordinates(lat=52.1, lon=4.3)
    stored = await db_session.scalar(
        text("SELECT ST_AsText(location::geometry) FROM caches WHERE gc_code = 'GC0001A'")
    )
    assert stored == "POINT(4.3 52.1)"


@pytest.mark.parametrize("correction", [None, Coordinates(53.2, 5.4)])
async def test_effective_location_prefers_correction_and_falls_back(
    db_session: AsyncSession, correction: Coordinates | None
) -> None:
    db_session.add(_cache_model())
    await db_session.flush()
    if correction is not None:
        db_session.add(
            UserCacheDataModel(
                cache_gc_code="GC0001A",
                note="Private note",
                corrected_location=coordinates_to_point(correction),
            )
        )
        await db_session.flush()
    statement = (
        select(effective_location())
        .select_from(CacheModel)
        .outerjoin(UserCacheDataModel)
        .order_by(effective_location())
    )
    location = (await db_session.execute(statement)).scalar_one()
    assert point_to_coordinates(location) == (correction or Coordinates(52.1, 4.3))
    if correction is not None:
        await db_session.execute(update(UserCacheDataModel).values(corrected_location=None))
        location = (await db_session.execute(statement)).scalar_one()
        assert point_to_coordinates(location) == Coordinates(52.1, 4.3)
        assert await db_session.scalar(select(UserCacheDataModel.note)) == "Private note"


async def test_import_history_preserves_waypoint_count_and_error_context(
    db_session: AsyncSession,
) -> None:
    issue = ImportIssue(
        severity="warning",
        file="synthetic.gpx",
        gc_code="GC0001A",
        line=12,
        code="unknown_type",
        message="Unknown source cache type",
    )
    db_session.add(
        ImportRunModel(
            source="pq", filenames=["synthetic.gpx"], waypoints=3, errors=[asdict(issue)]
        )
    )
    await db_session.flush()
    db_session.expire_all()
    run = (await db_session.scalars(select(ImportRunModel))).one()
    assert run.waypoints == 3
    assert run.errors == [asdict(issue)]
    assert run.started_at.tzinfo is not None
    assert run.filenames == ["synthetic.gpx"]


async def test_related_entities_persist_raw_types_and_nullable_waypoint_location(
    db_session: AsyncSession,
) -> None:
    cache = _cache_model()
    cache.waypoints = [
        CacheWaypointModel(
            code="RP0001A",
            name="Reference",
            type=WaypointType.OTHER,
            source_type="Future waypoint type",
            location=None,
        )
    ]
    cache.logs = [
        CacheLogModel(
            id=5_000_000_001,
            type=LogType.OTHER,
            source_type="Future log type",
            finder="Synthetic finder",
            logged_at=datetime(2026, 1, 1, tzinfo=UTC),
            text="Synthetic log",
        )
    ]
    cache.user_data = UserCacheDataModel(note="Keep separate")
    db_session.add(cache)
    await db_session.flush()
    created_at = cache.created_at
    await db_session.execute(update(CacheModel).values(name="Renamed"))
    db_session.expire_all()
    restored = (await db_session.scalars(select(CacheModel))).one()
    assert restored.created_at == created_at
    waypoint = (await db_session.scalars(select(CacheWaypointModel))).one()
    log = (await db_session.scalars(select(CacheLogModel))).one()
    assert waypoint.source_type == "Future waypoint type"
    assert waypoint.location is None
    assert log.id == 5_000_000_001
    assert log.source_type == "Future log type"
    assert log.type == "Other"
    assert await db_session.scalar(select(UserCacheDataModel.note)) == "Keep separate"
