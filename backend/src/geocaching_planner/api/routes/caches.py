"""Cache list and viewport-marker endpoints."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from geocaching_planner.adapters.db.cache_repository import SqlAlchemyCacheRepository
from geocaching_planner.adapters.db.settings_repository import SqlAlchemySettingsRepository
from geocaching_planner.api.cache_filters import CacheFilterDep, MarkerCacheFilterDep
from geocaching_planner.api.deps import SessionDep
from geocaching_planner.domain.cache_filter import CachePageRequest, CacheSort
from geocaching_planner.services.cache_query import CacheQueryService

router = APIRouter(tags=["caches"])
MARKER_CAP = 20_000
CacheSortName = Literal[
    "name",
    "-name",
    "gc_code",
    "-gc_code",
    "difficulty",
    "-difficulty",
    "terrain",
    "-terrain",
    "distance",
    "-distance",
    "placed_at",
    "-placed_at",
]


class CacheSummaryResponse(BaseModel):
    gc_code: str
    name: str
    type: str
    container: str
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


class CachePageResponse(BaseModel):
    items: list[CacheSummaryResponse]
    total: int


MarkerItemResponse = tuple[
    str,
    str,
    float,
    float,
    str,
    str,
    float,
    float,
    bool,
    bool,
    bool,
    bool,
]


class CacheMarkersResponse(BaseModel):
    items: list[MarkerItemResponse]
    truncated: bool
    total: int


def get_marker_cap(request: Request) -> int:
    cap = getattr(request.app.state, "marker_cap", MARKER_CAP)
    if not isinstance(cap, int) or cap < 1:
        raise RuntimeError("The configured marker cap must be a positive integer.")
    return cap


MarkerCapDep = Annotated[int, Depends(get_marker_cap)]


def _service(session: SessionDep) -> CacheQueryService:
    return CacheQueryService(
        SqlAlchemyCacheRepository(session),
        SqlAlchemySettingsRepository(session),
    )


@router.get("/caches/markers", response_model=CacheMarkersResponse)
async def get_cache_markers(
    session: SessionDep,
    cache_filter: MarkerCacheFilterDep,
    marker_cap: MarkerCapDep,
) -> CacheMarkersResponse:
    result = await _service(session).markers(cache_filter, marker_cap)
    return CacheMarkersResponse(
        items=[marker.as_tuple() for marker in result.items],
        truncated=result.truncated,
        total=result.total,
    )


@router.get("/caches", response_model=CachePageResponse)
async def list_caches(
    session: SessionDep,
    cache_filter: CacheFilterDep,
    sort: Annotated[CacheSortName, Query()] = "gc_code",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 50,
) -> CachePageResponse:
    result = await _service(session).query(
        cache_filter,
        CacheSort(sort),
        CachePageRequest(page=page, page_size=page_size),
    )
    return CachePageResponse(
        items=[
            CacheSummaryResponse(
                gc_code=item.gc_code,
                name=item.name,
                type=item.type.value,
                container=item.container.value,
                difficulty=item.difficulty,
                terrain=item.terrain,
                found_by_me=item.found_by_me,
                is_available=item.is_available,
                is_archived=item.is_archived,
                placed_at=item.placed_at,
                lat=item.lat,
                lon=item.lon,
                has_corrected=item.has_corrected,
                distance_km=item.distance_km,
            )
            for item in result.items
        ],
        total=result.total,
    )
