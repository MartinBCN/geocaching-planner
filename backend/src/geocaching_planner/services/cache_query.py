"""Use case for filtered cache lists and viewport markers."""

from dataclasses import replace

from geocaching_planner.domain.cache_filter import (
    CacheFilter,
    CacheMarkers,
    CachePage,
    CachePageRequest,
    CacheSort,
)
from geocaching_planner.domain.errors import HomeLocationRequiredError
from geocaching_planner.services.ports import CacheRepository, SettingsRepository


class CacheQueryService:
    def __init__(
        self, cache_repository: CacheRepository, settings_repository: SettingsRepository
    ) -> None:
        self._cache_repository = cache_repository
        self._settings_repository = settings_repository

    async def query(
        self, cache_filter: CacheFilter, sort: CacheSort, page: CachePageRequest
    ) -> CachePage:
        settings = await self._settings_repository.get()
        home_location = settings.home_location if settings is not None else None
        if (
            sort.field == "distance" or cache_filter.max_distance_km is not None
        ) and home_location is None:
            raise HomeLocationRequiredError(
                "Set a home location in Settings before filtering or sorting by distance."
            )
        return await self._cache_repository.query(
            replace(cache_filter, home_location=home_location), sort, page
        )

    async def markers(self, cache_filter: CacheFilter, cap: int) -> CacheMarkers:
        settings = await self._settings_repository.get()
        home_location = settings.home_location if settings is not None else None
        if cache_filter.max_distance_km is not None and home_location is None:
            raise HomeLocationRequiredError(
                "Set a home location in Settings before filtering by distance."
            )
        return await self._cache_repository.markers(
            replace(cache_filter, home_location=home_location), cap
        )
