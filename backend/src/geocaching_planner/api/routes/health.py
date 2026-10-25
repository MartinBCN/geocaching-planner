from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from geocaching_planner.services.health import HealthService

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    db: Literal["ok", "error"]


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    service: HealthService = request.app.state.health_service
    result = await service.check()
    return HealthResponse(status=result.status, version=result.version, db=result.db)
