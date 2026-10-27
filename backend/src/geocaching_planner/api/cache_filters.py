"""Shared cache query parameters for list, marker, export, and corridor endpoints."""

from typing import Annotated

from fastapi import Depends, HTTPException, Query

from geocaching_planner.domain.cache import CacheType, ContainerSize
from geocaching_planner.domain.cache_filter import BoundingBox, CacheFilter


async def cache_filter_dependency(
    types: Annotated[list[CacheType] | None, Query()] = None,
    containers: Annotated[list[ContainerSize] | None, Query()] = None,
    difficulty_min: Annotated[float | None, Query(ge=1, le=5)] = None,
    difficulty_max: Annotated[float | None, Query(ge=1, le=5)] = None,
    terrain_min: Annotated[float | None, Query(ge=1, le=5)] = None,
    terrain_max: Annotated[float | None, Query(ge=1, le=5)] = None,
    found: bool | None = None,
    include_archived: bool = False,
    include_disabled: bool = True,
    max_distance_km: Annotated[float | None, Query(ge=0)] = None,
    bbox: str | None = None,
    text: str | None = None,
) -> CacheFilter:
    try:
        return CacheFilter(
            types=tuple(types or ()),
            containers=tuple(containers or ()),
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            terrain_min=terrain_min,
            terrain_max=terrain_max,
            found=found,
            include_archived=include_archived,
            include_disabled=include_disabled,
            max_distance_km=max_distance_km,
            bbox=_parse_bbox(bbox) if bbox is not None else None,
            text=text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _parse_bbox(value: str) -> BoundingBox:
    parts = value.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must contain minLon,minLat,maxLon,maxLat.")
    try:
        coordinates = tuple(float(part) for part in parts)
        return BoundingBox(*coordinates)
    except ValueError as exc:
        raise ValueError(
            "bbox must contain four finite, ordered longitude/latitude coordinates."
        ) from exc


CacheFilterDep = Annotated[CacheFilter, Depends(cache_filter_dependency)]


async def marker_cache_filter_dependency(
    bbox: str,
    types: Annotated[list[CacheType] | None, Query()] = None,
    containers: Annotated[list[ContainerSize] | None, Query()] = None,
    difficulty_min: Annotated[float | None, Query(ge=1, le=5)] = None,
    difficulty_max: Annotated[float | None, Query(ge=1, le=5)] = None,
    terrain_min: Annotated[float | None, Query(ge=1, le=5)] = None,
    terrain_max: Annotated[float | None, Query(ge=1, le=5)] = None,
    found: bool | None = None,
    include_archived: bool = False,
    include_disabled: bool = True,
    max_distance_km: Annotated[float | None, Query(ge=0)] = None,
    text: str | None = None,
) -> CacheFilter:
    return await cache_filter_dependency(
        types=types,
        containers=containers,
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        terrain_min=terrain_min,
        terrain_max=terrain_max,
        found=found,
        include_archived=include_archived,
        include_disabled=include_disabled,
        max_distance_km=max_distance_km,
        bbox=bbox,
        text=text,
    )


MarkerCacheFilterDep = Annotated[CacheFilter, Depends(marker_cache_filter_dependency)]
