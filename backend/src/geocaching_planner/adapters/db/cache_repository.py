"""PostGIS implementation of the cache repository contract."""

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Literal, cast

from geoalchemy2.elements import WKBElement
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from geocaching_planner.adapters.db.models import (
    CacheLogModel,
    CacheModel,
    CacheWaypointModel,
    ImportRunModel,
    UserCacheDataModel,
)
from geocaching_planner.adapters.db.spatial import coordinates_to_point, point_to_coordinates
from geocaching_planner.domain.cache import (
    Cache,
    CacheAttribute,
    CacheLog,
    CacheType,
    CacheWaypoint,
    ContainerSize,
    ImportIssue,
    ImportRun,
    LogType,
    UnsetField,
    UserCacheData,
    UserCacheDataUpdate,
    WaypointType,
)
from geocaching_planner.domain.errors import NotFoundError
from geocaching_planner.services.ports import UpsertResult


class SqlAlchemyCacheRepository:
    """Each write method commits atomically; an upsert call is one import batch."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, caches: Sequence[Cache]) -> UpsertResult:
        # A duplicate GC code in one input batch is resolved before PostgreSQL sees it.
        latest = {cache.gc_code: cache for cache in caches}
        if not latest:
            return UpsertResult(created=(), updated=(), unchanged=(), waypoint_count=0)

        cache_list = list(latest.values())
        gc_codes = list(latest)
        waypoint_count = sum(
            len(cache.waypoints) for cache in cache_list if cache.waypoints is not None
        )
        try:
            existing_rows = await self._session.execute(
                select(CacheModel.gc_code, CacheModel.source_hash).where(
                    CacheModel.gc_code.in_(gc_codes)
                )
            )
            existing_hashes = dict(existing_rows.all())

            insert_statement = insert(CacheModel).values(
                [_cache_values(cache) for cache in cache_list]
            )
            excluded = insert_statement.excluded
            update_values = {
                column.name: getattr(excluded, column.name)
                for column in CacheModel.__table__.columns
                if column.name not in {"gc_code", "created_at", "updated_at"}
            }
            update_values["updated_at"] = func.clock_timestamp()
            upsert_statement = insert_statement.on_conflict_do_update(
                index_elements=[CacheModel.gc_code],
                set_=update_values,
                where=CacheModel.source_hash.is_distinct_from(excluded.source_hash),
            ).returning(CacheModel.gc_code)
            changed_codes = list((await self._session.execute(upsert_statement)).scalars().all())

            created = tuple(code for code in changed_codes if code not in existing_hashes)
            updated = tuple(code for code in changed_codes if code in existing_hashes)
            changed_set = set(changed_codes)
            unchanged = tuple(code for code in gc_codes if code not in changed_set)

            await self._replace_waypoints(cache_list, changed_set)
            await self._upsert_logs(cache_list)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return UpsertResult(
            created=created,
            updated=updated,
            unchanged=unchanged,
            waypoint_count=waypoint_count,
        )

    async def get(self, gc_code: str) -> Cache | None:
        result = await self._session.execute(
            select(CacheModel)
            .options(selectinload(CacheModel.waypoints), selectinload(CacheModel.logs))
            .where(CacheModel.gc_code == gc_code)
            .execution_options(populate_existing=True)
        )
        row = result.scalar_one_or_none()
        return _cache_from_model(row) if row is not None else None

    async def get_user_data(self, gc_code: str) -> UserCacheData | None:
        row = await self._session.get(UserCacheDataModel, gc_code)
        return _user_data_from_model(row) if row is not None else None

    async def set_user_data(self, gc_code: str, update: UserCacheDataUpdate) -> UserCacheData:
        cache = await self._session.get(CacheModel, gc_code)
        if cache is None:
            raise NotFoundError(f"Cache {gc_code} was not found")

        insert_values: dict[str, object] = {"cache_gc_code": gc_code}
        update_values: dict[str, object] = {}
        if update.note is not UnsetField.UNSET:
            note = "" if update.note is None else update.note
            insert_values["note"] = note
            update_values["note"] = note
        if update.corrected_location is not UnsetField.UNSET:
            location = update.corrected_location
            point = coordinates_to_point(location) if location is not None else None
            insert_values["corrected_location"] = point
            update_values["corrected_location"] = point
        try:
            insert_statement = insert(UserCacheDataModel).values(**insert_values)
            upsert_statement = insert_statement.on_conflict_do_update(
                index_elements=[UserCacheDataModel.cache_gc_code],
                set_=update_values,
            ).returning(UserCacheDataModel)
            row = (await self._session.execute(upsert_statement)).scalar_one()
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _user_data_from_model(row)

    async def add_import_run(self, run: ImportRun) -> ImportRun:
        row = ImportRunModel(
            started_at=run.started_at,
            finished_at=run.finished_at,
            source=run.source,
            filenames=list(run.filenames),
            created=run.created,
            updated=run.updated,
            unchanged=run.unchanged,
            waypoints=run.waypoints,
            errors=[asdict(issue) for issue in run.errors],
        )
        try:
            self._session.add(row)
            await self._session.commit()
            await self._session.refresh(row)
        except Exception:
            await self._session.rollback()
            raise
        return _import_run_from_model(row)

    async def list_import_runs(self) -> Sequence[ImportRun]:
        rows = await self._session.scalars(
            select(ImportRunModel).order_by(
                ImportRunModel.started_at.desc(), ImportRunModel.id.desc()
            )
        )
        return tuple(_import_run_from_model(row) for row in rows)

    async def _replace_waypoints(self, caches: Sequence[Cache], changed: set[str]) -> None:
        replacements = [
            cache for cache in caches if cache.gc_code in changed and cache.waypoints is not None
        ]
        if not replacements:
            return
        codes = [cache.gc_code for cache in replacements]
        await self._session.execute(
            delete(CacheWaypointModel).where(CacheWaypointModel.cache_gc_code.in_(codes))
        )
        self._session.add_all(
            [
                CacheWaypointModel(
                    cache_gc_code=cache.gc_code,
                    prefix=waypoint.prefix,
                    code=waypoint.code,
                    name=waypoint.name,
                    type=waypoint.type.value,
                    source_type=waypoint.source_type,
                    location=(
                        coordinates_to_point(waypoint.location)
                        if waypoint.location is not None
                        else None
                    ),
                    description=waypoint.description,
                )
                for cache in replacements
                for waypoint in cache.waypoints or ()
            ]
        )

    async def _upsert_logs(self, caches: Sequence[Cache]) -> None:
        logs = {log.id: log for cache in caches for log in cache.logs}
        if not logs:
            return
        values = [
            {
                "id": log.id,
                "cache_gc_code": log.cache_gc_code,
                "type": log.type.value,
                "source_type": log.source_type,
                "finder": log.finder,
                "logged_at": log.logged_at,
                "text": log.text,
            }
            for log in logs.values()
        ]
        statement = insert(CacheLogModel).values(values)
        excluded = statement.excluded
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[CacheLogModel.id],
                set_={
                    "cache_gc_code": excluded.cache_gc_code,
                    "type": excluded.type,
                    "source_type": excluded.source_type,
                    "finder": excluded.finder,
                    "logged_at": excluded.logged_at,
                    "text": excluded.text,
                },
            )
        )


def _import_run_from_model(row: ImportRunModel) -> ImportRun:
    return ImportRun(
        id=row.id,
        started_at=row.started_at,
        finished_at=row.finished_at,
        source=row.source,
        filenames=tuple(row.filenames),
        created=row.created,
        updated=row.updated,
        unchanged=row.unchanged,
        waypoints=row.waypoints,
        errors=tuple(_issue_from_json(issue) for issue in row.errors),
    )


def _cache_values(cache: Cache) -> dict[str, object]:
    return {
        "gc_code": cache.gc_code,
        "name": cache.name,
        "type": cache.type.value,
        "source_type": cache.source_type,
        "container": cache.container.value,
        "source_container": cache.source_container,
        "difficulty": cache.difficulty,
        "terrain": cache.terrain,
        "owner": cache.owner,
        "placed_at": cache.placed_at,
        "location": coordinates_to_point(cache.location),
        "country": cache.country,
        "state": cache.state,
        "short_description": cache.short_description,
        "long_description": cache.long_description,
        "description_is_html": cache.description_is_html,
        "hint": cache.hint,
        "attributes": [asdict(attribute) for attribute in cache.attributes],
        "is_available": cache.is_available,
        "is_archived": cache.is_archived,
        "found_by_me": cache.found_by_me,
        "found_at": cache.found_at,
        "source": cache.source,
        "source_updated_at": cache.source_updated_at,
        "source_hash": cache.source_hash,
    }


def _cache_from_model(row: CacheModel) -> Cache:
    attributes = tuple(
        CacheAttribute(
            id=int(attribute["id"]),
            included=bool(attribute["included"]),
            text=str(attribute["text"]),
        )
        for attribute in row.attributes
    )
    waypoints = tuple(
        CacheWaypoint(
            id=waypoint.id,
            cache_gc_code=waypoint.cache_gc_code,
            prefix=waypoint.prefix,
            code=waypoint.code,
            name=waypoint.name,
            type=WaypointType(waypoint.type),
            source_type=waypoint.source_type,
            location=(
                point_to_coordinates(waypoint.location)
                if isinstance(waypoint.location, WKBElement)
                else None
            ),
            description=waypoint.description,
        )
        for waypoint in sorted(row.waypoints, key=lambda item: item.code)
    )
    logs = tuple(
        CacheLog(
            id=log.id,
            cache_gc_code=log.cache_gc_code,
            type=LogType(log.type),
            source_type=log.source_type,
            finder=log.finder,
            logged_at=log.logged_at,
            text=log.text,
        )
        for log in sorted(row.logs, key=lambda item: item.id)
    )
    return Cache(
        gc_code=row.gc_code,
        name=row.name,
        type=CacheType(row.type),
        container=ContainerSize(row.container),
        difficulty=row.difficulty,
        terrain=row.terrain,
        owner=row.owner,
        location=point_to_coordinates(row.location),
        source_type=row.source_type,
        source_container=row.source_container,
        placed_at=row.placed_at,
        country=row.country,
        state=row.state,
        short_description=row.short_description,
        long_description=row.long_description,
        description_is_html=row.description_is_html,
        hint=row.hint,
        attributes=attributes,
        is_available=row.is_available,
        is_archived=row.is_archived,
        found_by_me=row.found_by_me,
        found_at=row.found_at,
        source=row.source,
        source_updated_at=row.source_updated_at,
        waypoints=waypoints,
        logs=logs,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _user_data_from_model(row: UserCacheDataModel) -> UserCacheData:
    location = (
        point_to_coordinates(row.corrected_location)
        if isinstance(row.corrected_location, WKBElement)
        else None
    )
    return UserCacheData(
        cache_gc_code=row.cache_gc_code,
        note=row.note,
        corrected_location=location,
    )


def _issue_from_json(value: Mapping[str, str | int | None]) -> ImportIssue:
    severity = str(value["severity"])
    if severity not in {"warning", "error"}:
        raise ValueError(f"Invalid import issue severity: {severity}")
    gc_code = value.get("gc_code")
    line = value.get("line")
    if line is None:
        line_number = None
    elif isinstance(line, int):
        line_number = line
    else:
        line_number = int(line)
    return ImportIssue(
        severity=cast(Literal["warning", "error"], severity),
        file=str(value["file"]),
        gc_code=str(gc_code) if gc_code is not None else None,
        line=line_number,
        code=str(value["code"]),
        message=str(value["message"]),
    )
