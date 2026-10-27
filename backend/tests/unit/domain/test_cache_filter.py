import pytest

from geocaching_planner.domain.cache import CacheType, ContainerSize, Coordinates
from geocaching_planner.domain.cache_filter import BoundingBox, CacheFilter, CachePageRequest


def test_cache_filter_accepts_complete_enum_values_and_inclusive_bounds() -> None:
    cache_filter = CacheFilter(
        types=(CacheType.TRADITIONAL, CacheType.MYSTERY),
        containers=(ContainerSize.MICRO, ContainerSize.SMALL),
        difficulty_min=1.5,
        difficulty_max=4.5,
        terrain_min=2,
        terrain_max=5,
        found=False,
        include_archived=True,
        include_disabled=False,
        max_distance_km=0,
        bbox=BoundingBox(min_lon=4, min_lat=52, max_lon=5, max_lat=53),
        text="  GCabc  ",
        home_location=Coordinates(lat=52.1, lon=4.3),
    )

    assert cache_filter.types == (CacheType.TRADITIONAL, CacheType.MYSTERY)
    assert cache_filter.containers == (ContainerSize.MICRO, ContainerSize.SMALL)
    assert cache_filter.found is False
    assert cache_filter.max_distance_km == 0
    assert cache_filter.text == "GCabc"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("difficulty_min", 0.5),
        ("difficulty_max", 5.5),
        ("difficulty_min", 2.25),
        ("terrain_min", float("nan")),
        ("terrain_max", float("inf")),
        ("max_distance_km", -0.1),
        ("max_distance_km", float("nan")),
    ],
)
def test_cache_filter_rejects_invalid_numeric_ranges(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=r"between|greater than"):
        _cache_filter_with_invalid_value(field, value)


@pytest.mark.parametrize(
    ("minimum", "maximum", "field"),
    [
        (4, 3, "difficulty"),
        (5, 1, "terrain"),
    ],
)
def test_cache_filter_rejects_minimum_above_maximum(
    minimum: float, maximum: float, field: str
) -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        _cache_filter_with_invalid_range(minimum, maximum, field)


def _cache_filter_with_invalid_value(field: str, value: float) -> CacheFilter:
    if field == "difficulty_min":
        return CacheFilter(difficulty_min=value)
    if field == "difficulty_max":
        return CacheFilter(difficulty_max=value)
    if field == "terrain_min":
        return CacheFilter(terrain_min=value)
    if field == "terrain_max":
        return CacheFilter(terrain_max=value)
    return CacheFilter(max_distance_km=value)


def _cache_filter_with_invalid_range(minimum: float, maximum: float, field: str) -> CacheFilter:
    if field == "difficulty":
        return CacheFilter(difficulty_min=minimum, difficulty_max=maximum)
    return CacheFilter(terrain_min=minimum, terrain_max=maximum)


@pytest.mark.parametrize(
    "values",
    [
        (181, 0, 182, 1),
        (0, -91, 1, -90),
        (2, 1, 1, 2),
        (1, 2, 2, 1),
        (0, 0, 0, 1),
    ],
)
def test_bounding_box_rejects_out_of_range_or_unordered_coordinates(
    values: tuple[float, float, float, float],
) -> None:
    with pytest.raises(ValueError, match="bbox"):
        BoundingBox(*values)


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 1), (1, 0), (1, 501)],
)
def test_cache_page_request_rejects_invalid_ranges(page: int, page_size: int) -> None:
    with pytest.raises(ValueError, match="page"):
        CachePageRequest(page, page_size)
