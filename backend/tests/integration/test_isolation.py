from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_committed_rows_do_not_leak_between_tests(db_session: AsyncSession) -> None:
    """AC4 (test A): insert and commit a row; the per-test transaction is rolled back later."""
    await db_session.execute(text("INSERT INTO isolation_probe (note) VALUES ('leak-check')"))
    await db_session.commit()

    count = (await db_session.execute(text("SELECT count(*) FROM isolation_probe"))).scalar_one()
    assert count == 1


async def test_next_test_starts_with_empty_isolation_table(db_session: AsyncSession) -> None:
    """AC4 (test B): runs after test A and must see an empty table."""
    count = (await db_session.execute(text("SELECT count(*) FROM isolation_probe"))).scalar_one()
    assert count == 0
