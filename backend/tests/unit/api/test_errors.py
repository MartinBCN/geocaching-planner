from http import HTTPStatus
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, Response
from pydantic import BaseModel
from structlog.testing import capture_logs

from geocaching_planner.domain.errors import NotFoundError


class Item(BaseModel):
    name: str
    count: int


def _boom() -> None:
    raise RuntimeError("secret-xyz")


def _missing() -> None:
    raise NotFoundError("cache GC123 not found")


async def _create(item: Item) -> Item:
    return item


@pytest.fixture
def routed_app(app: FastAPI) -> FastAPI:
    app.add_api_route("/test/boom", _boom, methods=["GET"])
    app.add_api_route("/test/missing", _missing, methods=["GET"])
    app.add_api_route("/test/items", _create, methods=["POST"])
    return app


def assert_problem(response: Response, status: int, title: str) -> dict[str, Any]:
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body: dict[str, Any] = response.json()
    assert body["type"] == "about:blank"
    assert body["title"] == title
    assert body["status"] == status
    assert body["detail"]
    assert body["instance"]
    return body


async def test_unknown_route_and_method_not_allowed_use_problem(client: AsyncClient) -> None:
    not_found = await client.get("/does-not-exist")
    method = await client.post("/api/v1/health")

    assert_problem(not_found, 404, "Not Found")
    assert_problem(method, 405, "Method Not Allowed")


async def test_validation_errors_use_field_error_list(
    routed_app: FastAPI, client: AsyncClient
) -> None:
    response = await client.post("/test/items", json={"count": "many"})

    body = assert_problem(response, 422, HTTPStatus(422).phrase)
    fields = {error["field"] for error in body["errors"]}
    assert fields == {"name", "count"}
    assert all(set(error) == {"field", "message"} for error in body["errors"])


async def test_unhandled_error_is_safe_logged_and_correlated(
    routed_app: FastAPI, lenient_client: AsyncClient
) -> None:
    with capture_logs() as logs:
        response = await lenient_client.get("/test/boom")

    body = assert_problem(response, 500, "Internal Server Error")
    assert "secret-xyz" not in response.text
    assert "Traceback" not in response.text

    errors = [entry for entry in logs if entry["event"] == "unhandled_error"]
    assert len(errors) == 1
    assert isinstance(errors[0]["exc_info"], RuntimeError)
    assert body["instance"] == f"urn:request:{errors[0]['request_id']}"


async def test_domain_not_found_maps_to_404_problem(
    routed_app: FastAPI, client: AsyncClient
) -> None:
    response = await client.get("/test/missing")

    body = assert_problem(response, 404, "Not Found")
    assert body["detail"] == "cache GC123 not found"
