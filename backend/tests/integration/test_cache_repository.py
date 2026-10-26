from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.adapters.db.cache_repository import SqlAlchemyCacheRepository
from geocaching_planner.adapters.db.models import ImportRunModel
from tests.shared.cache_repository_suite import run_shared_behavior_suite


async def test_postgis_repository_shared_behavior_suite(db_session: AsyncSession) -> None:
    await run_shared_behavior_suite(SqlAlchemyCacheRepository(db_session))


async def test_import_run_errors_round_trip_as_json(db_session: AsyncSession) -> None:
    repository = SqlAlchemyCacheRepository(db_session)
    await run_shared_behavior_suite(repository)

    result = await db_session.execute(select(ImportRunModel).order_by(ImportRunModel.id.desc()))
    rows = result.scalars().all()
    assert rows
    assert rows[-1].errors == [
        {
            "severity": "warning",
            "file": "synthetic.gpx",
            "gc_code": "GC-SHARED",
            "line": 12,
            "code": "unmatched-waypoint",
            "message": "Waypoint has no cache parent.",
        }
    ]
