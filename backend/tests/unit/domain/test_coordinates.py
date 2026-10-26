import math
from dataclasses import FrozenInstanceError, fields

import pytest

from geocaching_planner.domain.cache import Coordinates


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (90.1, 0),
        (-90.1, 0),
        (0, 180.1),
        (0, -180.1),
        (math.nan, 0),
        (math.inf, 0),
        (-math.inf, 0),
        (0, math.nan),
        (0, math.inf),
        (0, -math.inf),
    ],
)
def test_invalid_coordinates_raise_value_error(lat: float, lon: float) -> None:
    with pytest.raises(ValueError, match=r"Latitude|Longitude"):
        Coordinates(lat, lon)


@pytest.mark.parametrize(("lat", "lon"), [(90, 180), (-90, -180), (0, 0), (52.1, 4.3)])
def test_boundary_and_asymmetric_coordinates_are_accepted(lat: float, lon: float) -> None:
    point = Coordinates(lat, lon)
    assert point.lat == lat
    assert point.lon == lon


def test_coordinates_are_immutable() -> None:
    point = Coordinates(52.1, 4.3)
    with pytest.raises(FrozenInstanceError):
        setattr(point, fields(point)[0].name, 0)
