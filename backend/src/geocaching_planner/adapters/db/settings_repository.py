"""PostGIS persistence for planner settings."""

from geoalchemy2.elements import WKBElement, WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.models import SettingsModel
from geocaching_planner.adapters.db.spatial import coordinates_to_point, point_to_coordinates
from geocaching_planner.domain.settings import BikeProfile, PlannerSettings


class SqlAlchemySettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> PlannerSettings | None:
        row = await self._session.get(SettingsModel, 1)
        return _to_domain(row) if row is not None else None

    async def save(self, settings: PlannerSettings) -> PlannerSettings:
        row = await self._session.get(SettingsModel, 1)
        if row is None:
            row = SettingsModel(id=1)
            self._session.add(row)

        row.home_location = (
            coordinates_to_point(settings.home_location)
            if settings.home_location is not None
            else None
        )
        row.avg_speed_kmh = settings.avg_speed_kmh
        row.corridor_m_default = settings.corridor_m_default
        row.default_profile = settings.default_profile.value
        row.tile_url = settings.tile_url
        row.tile_attribution = settings.tile_attribution
        await self._session.flush()
        await self._session.refresh(row, attribute_names=["home_location"])
        await self._session.commit()
        return _to_domain(row)


def _to_domain(row: SettingsModel) -> PlannerSettings:
    point = row.home_location
    if isinstance(point, WKTElement):
        raise RuntimeError("Settings location was not refreshed from the database")
    location = point_to_coordinates(point) if isinstance(point, WKBElement) else None
    return PlannerSettings(
        home_location=location,
        avg_speed_kmh=row.avg_speed_kmh,
        corridor_m_default=row.corridor_m_default,
        default_profile=BikeProfile(row.default_profile),
        tile_url=row.tile_url,
        tile_attribution=row.tile_attribution,
    )
