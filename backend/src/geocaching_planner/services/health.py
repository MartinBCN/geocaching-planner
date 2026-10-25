from dataclasses import dataclass
from typing import Literal, Protocol


class DatabaseProbe(Protocol):
    async def ping(self) -> bool: ...


@dataclass(frozen=True)
class HealthResult:
    status: Literal["ok", "degraded"]
    version: str
    db: Literal["ok", "error"]


class HealthService:
    """Reports overall health. A failing database degrades status but never raises."""

    def __init__(self, probe: DatabaseProbe, version: str) -> None:
        self._probe = probe
        self._version = version

    async def check(self) -> HealthResult:
        db_ok = await self._probe.ping()
        return HealthResult(
            status="ok" if db_ok else "degraded",
            version=self._version,
            db="ok" if db_ok else "error",
        )
