from http import HTTPStatus
from typing import Any

from pydantic import BaseModel
from starlette.responses import JSONResponse

PROBLEM_MEDIA_TYPE = "application/problem+json"


class FieldError(BaseModel):
    field: str
    message: str


class Problem(BaseModel):
    """RFC 9457 problem details."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str


class ValidationProblem(Problem):
    errors: list[FieldError]


def problem_response(
    *,
    status: int,
    detail: str,
    instance: str,
    headers: dict[str, str] | None = None,
    errors: list[FieldError] | None = None,
) -> JSONResponse:
    title = HTTPStatus(status).phrase
    body: dict[str, Any]
    if errors is None:
        body = Problem(title=title, status=status, detail=detail, instance=instance).model_dump()
    else:
        body = ValidationProblem(
            title=title, status=status, detail=detail, instance=instance, errors=errors
        ).model_dump()
    return JSONResponse(body, status_code=status, media_type=PROBLEM_MEDIA_TYPE, headers=headers)
