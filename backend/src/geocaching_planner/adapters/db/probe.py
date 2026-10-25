import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

PING_TIMEOUT_SECONDS = 2


class SqlAlchemyProbe:
    """Checks database reachability with a bounded `SELECT 1`."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def ping(self) -> bool:
        try:
            async with asyncio.timeout(PING_TIMEOUT_SECONDS), self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except OSError, SQLAlchemyError, TimeoutError:
            return False
        return True
