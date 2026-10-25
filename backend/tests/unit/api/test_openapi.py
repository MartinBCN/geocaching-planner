from httpx import AsyncClient

PROBLEM_REF = {"$ref": "#/components/schemas/Problem"}


async def test_openapi_declares_problem_responses(client: AsyncClient) -> None:
    response = await client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    spec = response.json()
    assert "/api/v1/health" in spec["paths"]
    assert "Problem" in spec["components"]["schemas"]

    responses = spec["paths"]["/api/v1/health"]["get"]["responses"]
    for status in ("404", "405", "422", "500"):
        content = responses[status]["content"]
        assert set(content) == {"application/problem+json"}
        assert content["application/problem+json"]["schema"] == PROBLEM_REF
