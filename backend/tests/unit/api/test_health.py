from importlib.metadata import version

from httpx import AsyncClient


async def test_health_uses_package_version(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("geocaching-planner")}
