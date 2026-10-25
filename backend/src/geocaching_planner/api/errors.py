from http import HTTPStatus

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from geocaching_planner.api.middleware import get_request_id
from geocaching_planner.api.problem import FieldError, problem_response
from geocaching_planner.domain.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    UpstreamUnavailableError,
)

logger = structlog.get_logger(__name__)

DOMAIN_STATUS: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
    UpstreamUnavailableError: 503,
}

INTERNAL_ERROR_DETAIL = (
    "An unexpected error occurred. Quote the instance identifier when reporting it."
)


def _instance(request: Request) -> str:
    return f"urn:request:{get_request_id(request)}"


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status = 500
    detail = ""
    headers: dict[str, str] | None = None
    if isinstance(exc, StarletteHTTPException):
        status = exc.status_code
        detail = exc.detail if isinstance(exc.detail, str) else ""
        headers = dict(exc.headers) if exc.headers else None
    return problem_response(
        status=status,
        detail=detail or HTTPStatus(status).phrase,
        instance=_instance(request),
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    errors: list[FieldError] = []
    if isinstance(exc, RequestValidationError):
        errors = [
            FieldError(
                field=".".join(str(part) for part in error["loc"] if part != "body") or "body",
                message=str(error["msg"]),
            )
            for error in exc.errors()
        ]
    return problem_response(
        status=422,
        detail="The request body or parameters failed validation.",
        instance=_instance(request),
        errors=errors,
    )


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status = 500
    if isinstance(exc, DomainError):
        status = next((code for cls, code in DOMAIN_STATUS.items() if isinstance(exc, cls)), 500)
    return problem_response(
        status=status,
        detail=str(exc) or HTTPStatus(status).phrase,
        instance=_instance(request),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    logger.error("unhandled_error", request_id=request_id, exc_info=exc)
    return problem_response(
        status=500,
        detail=INTERNAL_ERROR_DETAIL,
        instance=f"urn:request:{request_id}",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
