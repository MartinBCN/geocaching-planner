"""User-configurable planner defaults."""

import math
from dataclasses import dataclass
from enum import StrEnum

from geocaching_planner.domain.cache import Coordinates


class BikeProfile(StrEnum):
    TREKKING = "trekking"
    FASTBIKE = "fastbike"
    SAFETY = "safety"


@dataclass(frozen=True)
class PlannerSettings:
    home_location: Coordinates | None = None
    avg_speed_kmh: float = 18.0
    corridor_m_default: int = 500
    default_profile: BikeProfile = BikeProfile.TREKKING
    tile_url: str | None = None
    tile_attribution: str = "© OpenStreetMap contributors, CyclOSM"

    def __post_init__(self) -> None:
        if not math.isfinite(self.avg_speed_kmh) or not 5 <= self.avg_speed_kmh <= 50:
            raise ValueError("Average speed must be between 5 and 50 km/h")
        if not 50 <= self.corridor_m_default <= 5000:
            raise ValueError("Default corridor must be between 50 and 5000 meters")
