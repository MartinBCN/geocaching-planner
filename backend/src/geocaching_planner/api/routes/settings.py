from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from geocaching_planner.adapters.db.settings_repository import SqlAlchemySettingsRepository
from geocaching_planner.api.deps import SessionDep, SettingsDep
from geocaching_planner.domain.cache import Coordinates
from geocaching_planner.domain.settings import BikeProfile, PlannerSettings
from geocaching_planner.services.settings import SettingsService

router = APIRouter(tags=["settings"])


class CoordinatesModel(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class SettingsPayload(BaseModel):
    home_location: CoordinatesModel | None = None
    avg_speed_kmh: float = Field(default=18, ge=5, le=50, allow_inf_nan=False)
    corridor_m_default: int = Field(default=500, ge=50, le=5000)
    default_profile: Literal["trekking", "fastbike", "safety"] = "trekking"
    tile_url: str | None = Field(default=None, max_length=2048)
    tile_attribution: str = Field(
        default="© OpenStreetMap contributors, CyclOSM", min_length=1, max_length=500
    )

    @field_validator("tile_url")
    @classmethod
    def validate_tile_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("Tile URL must use HTTP or HTTPS")
        return value


class SettingsResponse(BaseModel):
    home_location: CoordinatesModel | None
    avg_speed_kmh: float
    corridor_m_default: int
    default_profile: Literal["trekking", "fastbike", "safety"]
    tile_url: str
    tile_attribution: str


def _service(session: SessionDep, config: SettingsDep) -> SettingsService:
    return SettingsService(
        SqlAlchemySettingsRepository(session),
        default_tile_url=config.tile_url,
        default_tile_attribution=config.tile_attribution,
    )


def _response(settings: PlannerSettings, service: SettingsService) -> SettingsResponse:
    location = settings.home_location
    return SettingsResponse(
        home_location=(
            CoordinatesModel(lat=location.lat, lon=location.lon) if location is not None else None
        ),
        avg_speed_kmh=settings.avg_speed_kmh,
        corridor_m_default=settings.corridor_m_default,
        default_profile=settings.default_profile.value,
        tile_url=service.effective_tile_url(settings),
        tile_attribution=settings.tile_attribution,
    )


def _domain_settings(payload: SettingsPayload) -> PlannerSettings:
    location = payload.home_location
    return PlannerSettings(
        home_location=Coordinates(lat=location.lat, lon=location.lon) if location else None,
        avg_speed_kmh=payload.avg_speed_kmh,
        corridor_m_default=payload.corridor_m_default,
        default_profile=BikeProfile(payload.default_profile),
        tile_url=payload.tile_url,
        tile_attribution=payload.tile_attribution,
    )


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(session: SessionDep, config: SettingsDep) -> SettingsResponse:
    service = _service(session, config)
    return _response(await service.get_settings(), service)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    payload: SettingsPayload, session: SessionDep, config: SettingsDep
) -> SettingsResponse:
    service = _service(session, config)
    result = await service.update_settings(_domain_settings(payload))
    return _response(result, service)
