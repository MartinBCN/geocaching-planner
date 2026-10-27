"""PostGIS query composition for cache filters and effective locations."""

from typing import Any

from geoalchemy2 import Geography, Geometry
from sqlalchemy import Select, cast, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.models import CacheModel, UserCacheDataModel
from geocaching_planner.adapters.db.spatial import coordinates_to_point, effective_location
from geocaching_planner.domain.cache import CacheType, ContainerSize, Coordinates
from geocaching_planner.domain.cache_filter import (
    BoundingBox,
    CacheFilter,
    CacheMarker,
    CacheMarkers,
    CachePage,
    CachePageRequest,
    CacheSort,
    CacheSummary,
)


def apply_cache_filter[*SelectedColumns](
    statement: Select[*SelectedColumns], cache_filter: CacheFilter
) -> Select[*SelectedColumns]:
    """Apply non-spatial predicates and separate indexed corrected/original location branches."""
    if cache_filter.types:
        statement = statement.where(
            CacheModel.type.in_([value.value for value in cache_filter.types])
        )
    if cache_filter.containers:
        statement = statement.where(
            CacheModel.container.in_([value.value for value in cache_filter.containers])
        )
    if cache_filter.difficulty_min is not None:
        statement = statement.where(CacheModel.difficulty >= cache_filter.difficulty_min)
    if cache_filter.difficulty_max is not None:
        statement = statement.where(CacheModel.difficulty <= cache_filter.difficulty_max)
    if cache_filter.terrain_min is not None:
        statement = statement.where(CacheModel.terrain >= cache_filter.terrain_min)
    if cache_filter.terrain_max is not None:
        statement = statement.where(CacheModel.terrain <= cache_filter.terrain_max)
    if cache_filter.found is not None:
        statement = statement.where(CacheModel.found_by_me.is_(cache_filter.found))
    if not cache_filter.include_archived:
        statement = statement.where(CacheModel.is_archived.is_(False))
    if not cache_filter.include_disabled:
        statement = statement.where(CacheModel.is_available.is_(True))
    if cache_filter.text:
        text = cache_filter.text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(
            or_(
                CacheModel.gc_code.ilike(f"{text}%", escape="\\"),
                CacheModel.name.ilike(f"%{text}%", escape="\\"),
            )
        )
    if cache_filter.bbox is not None:
        statement = statement.where(CacheModel.gc_code.in_(_bbox_cache_codes(cache_filter.bbox)))
    if cache_filter.max_distance_km is not None:
        if cache_filter.home_location is None:
            raise ValueError("A home location is required for a distance filter.")
        statement = statement.where(
            CacheModel.gc_code.in_(
                _distance_cache_codes(
                    cache_filter.home_location,
                    cache_filter.max_distance_km * 1000,
                )
            )
        )
    return statement


def _bbox_cache_codes(bbox: BoundingBox) -> Any:
    envelope = func.ST_MakeEnvelope(
        bbox.min_lon,
        bbox.min_lat,
        bbox.max_lon,
        bbox.max_lat,
        4326,
        type_=Geometry(srid=4326),
    )
    bbox_geometry = Geometry(geometry_type="GEOMETRY")
    corrected = UserCacheDataModel.corrected_location.cast(bbox_geometry)
    original = CacheModel.location.cast(bbox_geometry)
    corrected_branch = select(UserCacheDataModel.cache_gc_code).where(
        UserCacheDataModel.corrected_location.is_not(None),
        corrected.op("&&")(envelope),
        func.ST_Intersects(corrected, envelope),
    )
    original_branch = (
        select(CacheModel.gc_code)
        .outerjoin(
            UserCacheDataModel,
            UserCacheDataModel.cache_gc_code == CacheModel.gc_code,
        )
        .where(
            UserCacheDataModel.corrected_location.is_(None),
            original.op("&&")(envelope),
            func.ST_Intersects(original, envelope),
        )
    )
    return union_all(corrected_branch, original_branch)


def _distance_cache_codes(home: Coordinates, distance_m: float) -> Any:
    home_point = cast(coordinates_to_point(home), Geography(srid=4326))
    corrected_branch = select(UserCacheDataModel.cache_gc_code).where(
        UserCacheDataModel.corrected_location.is_not(None),
        func.ST_DWithin(UserCacheDataModel.corrected_location, home_point, distance_m),
    )
    original_branch = (
        select(CacheModel.gc_code)
        .outerjoin(
            UserCacheDataModel,
            UserCacheDataModel.cache_gc_code == CacheModel.gc_code,
        )
        .where(
            UserCacheDataModel.corrected_location.is_(None),
            func.ST_DWithin(CacheModel.location, home_point, distance_m),
        )
    )
    return union_all(corrected_branch, original_branch)


class SqlAlchemyCacheQuery:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def query(
        self, cache_filter: CacheFilter, sort: CacheSort, page: CachePageRequest
    ) -> CachePage:
        distance = self._distance_expression(cache_filter)
        effective = effective_location()
        selected_distance = distance if distance is not None else literal(None)
        statement = (
            select(
                CacheModel.gc_code.label("gc_code"),
                CacheModel.name.label("name"),
                CacheModel.type.label("type"),
                CacheModel.container.label("container"),
                CacheModel.difficulty.label("difficulty"),
                CacheModel.terrain.label("terrain"),
                CacheModel.found_by_me.label("found_by_me"),
                CacheModel.is_available.label("is_available"),
                CacheModel.is_archived.label("is_archived"),
                CacheModel.placed_at.label("placed_at"),
                func.ST_Y(effective.cast(Geometry())).label("lat"),
                func.ST_X(effective.cast(Geometry())).label("lon"),
                UserCacheDataModel.corrected_location.is_not(None).label("has_corrected"),
                selected_distance.label("distance_km"),
            )
            .select_from(CacheModel)
            .outerjoin(
                UserCacheDataModel,
                UserCacheDataModel.cache_gc_code == CacheModel.gc_code,
            )
        )
        statement = apply_cache_filter(statement, cache_filter)
        total_statement = apply_cache_filter(
            select(func.count()).select_from(CacheModel), cache_filter
        )
        total = int(await self._session.scalar(total_statement) or 0)
        ordering: dict[str, Any] = {
            "name": func.lower(CacheModel.name),
            "gc_code": CacheModel.gc_code,
            "difficulty": CacheModel.difficulty,
            "terrain": CacheModel.terrain,
            "placed_at": CacheModel.placed_at,
            "distance": distance,
        }
        order_expression = ordering[sort.field]
        if sort.descending:
            order_expression = order_expression.desc().nulls_last()
        elif sort.field in {"placed_at", "distance"}:
            order_expression = order_expression.asc().nulls_last()
        paged_statement = (
            statement.order_by(order_expression, CacheModel.gc_code.asc())
            .offset((page.page - 1) * page.page_size)
            .limit(page.page_size)
        )
        rows = (await self._session.execute(paged_statement)).mappings().all()
        return CachePage(
            items=tuple(
                CacheSummary(
                    gc_code=row["gc_code"],
                    name=row["name"],
                    type=CacheType(row["type"]),
                    container=ContainerSize(row["container"]),
                    difficulty=row["difficulty"],
                    terrain=row["terrain"],
                    found_by_me=row["found_by_me"],
                    is_available=row["is_available"],
                    is_archived=row["is_archived"],
                    placed_at=row["placed_at"],
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    has_corrected=row["has_corrected"],
                    distance_km=(
                        float(row["distance_km"]) if row["distance_km"] is not None else None
                    ),
                )
                for row in rows
            ),
            total=total,
        )

    async def markers(self, cache_filter: CacheFilter, cap: int) -> CacheMarkers:
        if cap < 1:
            raise ValueError("Marker cap must be at least 1.")
        effective = effective_location()
        base_statement = (
            select(
                CacheModel.gc_code.label("gc_code"),
                CacheModel.name.label("name"),
                func.ST_Y(effective.cast(Geometry())).label("lat"),
                func.ST_X(effective.cast(Geometry())).label("lon"),
                CacheModel.type.label("type"),
                CacheModel.container.label("container"),
                CacheModel.difficulty.label("difficulty"),
                CacheModel.terrain.label("terrain"),
                CacheModel.found_by_me.label("found_by_me"),
                CacheModel.is_available.label("is_available"),
                CacheModel.is_archived.label("is_archived"),
                UserCacheDataModel.corrected_location.is_not(None).label("has_corrected"),
            )
            .select_from(CacheModel)
            .outerjoin(
                UserCacheDataModel,
                UserCacheDataModel.cache_gc_code == CacheModel.gc_code,
            )
        )
        base_statement = apply_cache_filter(base_statement, cache_filter)
        total_statement = apply_cache_filter(
            select(func.count()).select_from(CacheModel), cache_filter
        )
        total = int(await self._session.scalar(total_statement) or 0)
        rows = (
            (
                await self._session.execute(
                    base_statement.order_by(CacheModel.gc_code.asc()).limit(cap)
                )
            )
            .mappings()
            .all()
        )
        return CacheMarkers(
            items=tuple(
                CacheMarker(
                    gc_code=row["gc_code"],
                    name=row["name"],
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    type=CacheType(row["type"]),
                    container=ContainerSize(row["container"]),
                    difficulty=row["difficulty"],
                    terrain=row["terrain"],
                    found_by_me=row["found_by_me"],
                    is_available=row["is_available"],
                    is_archived=row["is_archived"],
                    has_corrected=row["has_corrected"],
                )
                for row in rows
            ),
            truncated=total > cap,
            total=total,
        )

    @staticmethod
    def _distance_expression(cache_filter: CacheFilter) -> Any | None:
        if cache_filter.home_location is None:
            return None
        home_point = cast(coordinates_to_point(cache_filter.home_location), Geography(srid=4326))
        return func.ST_Distance(effective_location(), home_point) / 1000
