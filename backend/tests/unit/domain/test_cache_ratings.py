from dataclasses import replace
from math import inf, nan

import pytest

from geocaching_planner.domain.cache import Cache


@pytest.mark.parametrize("value", [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
def test_half_step_ratings_are_accepted(cache: Cache, value: float) -> None:
    assert replace(cache, difficulty=value, terrain=value).difficulty == value


@pytest.mark.parametrize("value", [0, 0.5, 5.5, 1.1, 2.25, nan, inf, -inf])
def test_invalid_ratings_raise_value_error(cache: Cache, value: float) -> None:
    with pytest.raises(ValueError, match="difficulty"):
        replace(cache, difficulty=value)
    with pytest.raises(ValueError, match="terrain"):
        replace(cache, terrain=value)
