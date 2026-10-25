import asyncio
import socket
import time

from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

from geocaching_planner.config import AppConfig
from geocaching_planner.main import create_app


def _health(url: str) -> tuple[int, dict[str, str], float]:
    app = create_app(AppConfig(_env_file=None, database_url=url))

    async def _call() -> tuple[int, dict[str, str], float]:
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as http:
                started = time.monotonic()
                response = await http.get("/api/v1/health")
                elapsed = time.monotonic() - started
        return response.status_code, response.json(), elapsed

    return asyncio.run(_call())


def test_health_reports_ok_against_real_database(postgis_url: str) -> None:
    """AC3: an available database returns 200 with status ok and db ok."""
    status, body, _ = _health(postgis_url)

    assert status == 200
    assert body["status"] == "ok"
    assert body["db"] == "ok"


def test_closed_port_reports_degraded_quickly(postgis_url: str) -> None:
    """AC3: a closed-port database returns 200 degraded/error within three seconds."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        closed_port = sock.getsockname()[1]
    url = make_url(postgis_url).set(port=closed_port).render_as_string(hide_password=False)

    status, body, elapsed = _health(url)

    assert status == 200
    assert body["status"] == "degraded"
    assert body["db"] == "error"
    assert elapsed < 3
