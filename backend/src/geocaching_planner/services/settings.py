"""Settings use case."""

from geocaching_planner.domain.settings import PlannerSettings
from geocaching_planner.services.ports import SettingsRepository


class SettingsService:
    def __init__(
        self,
        repository: SettingsRepository,
        *,
        default_tile_url: str,
        default_tile_attribution: str,
    ) -> None:
        self._repository = repository
        self._defaults = PlannerSettings(tile_attribution=default_tile_attribution)
        self._default_tile_url = default_tile_url

    async def get_settings(self) -> PlannerSettings:
        settings = await self._repository.get()
        return settings if settings is not None else self._defaults

    async def update_settings(self, settings: PlannerSettings) -> PlannerSettings:
        return await self._repository.save(settings)

    def effective_tile_url(self, settings: PlannerSettings) -> str:
        return settings.tile_url or self._default_tile_url
