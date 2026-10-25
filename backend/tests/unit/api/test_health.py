from importlib.metadata import version

from httpx import AsyncClient

from geocaching_planner.config import AppConfig


async def test_health_uses_package_version(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": version("geocaching-planner"),
        "db": "ok",
    }


async def test_health_degrades_when_database_is_down(config: AppConfig) -> None:
    from httpx import ASGITransport

    from geocaching_planner.main import create_app
    from tests.conftest import FakeProbe

    app = create_app(config, database_probe=FakeProbe(healthy=False))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        response = await http.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["db"] == "error"
