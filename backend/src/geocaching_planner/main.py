from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from geocaching_planner import __version__
from geocaching_planner.api.errors import register_exception_handlers
from geocaching_planner.api.middleware import RequestIdMiddleware
from geocaching_planner.api.problem import PROBLEM_MEDIA_TYPE, Problem
from geocaching_planner.api.routes.health import router as health_router
from geocaching_planner.config import AppConfig
from geocaching_planner.logging_config import configure_logging

API_PREFIX = "/api/v1"
PROBLEM_SCHEMA_REF = {"$ref": f"#/components/schemas/{Problem.__name__}"}

COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"description": "Not found", "model": Problem},
    405: {"description": "Method not allowed", "model": Problem},
    422: {"description": "Validation error", "model": Problem},
    500: {"description": "Unexpected server error", "model": Problem},
}


def _advertise_problem_media_type(schema: dict[str, Any]) -> None:
    """Document error responses as application/problem+json only, with the Problem schema."""
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            for status, response in operation.get("responses", {}).items():
                if status[:1] not in {"4", "5"} or "content" not in response:
                    continue
                response["content"] = {PROBLEM_MEDIA_TYPE: {"schema": PROBLEM_SCHEMA_REF}}


class PlannerAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        if self.openapi_schema is None:
            schema = get_openapi(title=self.title, version=__version__, routes=self.routes)
            _advertise_problem_media_type(schema)
            self.openapi_schema = schema
        return self.openapi_schema


def create_app(config: AppConfig | None = None) -> FastAPI:
    settings = config if config is not None else AppConfig()
    configure_logging(json_logs=settings.log_json)

    app = PlannerAPI(
        title="Geocaching Planner",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
        responses=COMMON_RESPONSES,
    )
    app.state.config = settings
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router, prefix=API_PREFIX)
    return app
