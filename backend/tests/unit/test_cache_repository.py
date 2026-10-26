from datetime import UTC, datetime, timedelta

import pytest

from geocaching_planner.domain.cache import UserCacheDataUpdate
from tests.shared.cache_repository_suite import run_shared_behavior_suite
from tests.unit.fakes.cache_repository import FakeCacheRepository


@pytest.mark.asyncio
async def test_fake_repository_shared_behavior_suite() -> None:
    base = datetime(2025, 1, 1, tzinfo=UTC)
    ticks = iter(base + timedelta(seconds=second) for second in range(100))
    repository = FakeCacheRepository(clock=lambda: next(ticks))

    await run_shared_behavior_suite(repository)


def test_user_data_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValueError, match="At least one user-data field"):
        UserCacheDataUpdate()
