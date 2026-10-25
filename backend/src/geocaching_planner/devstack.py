"""Developer entry point: preflight checks, start the database, migrate, then run the backend.

Run through `mise run dev`. Fails fast (exit 1, before any service starts) when Docker is
unreachable or the configured DB_PORT is held by something other than this project's database.
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from alembic import command

from geocaching_planner.adapters.db.migrations import alembic_config
from geocaching_planner.config import AppConfig

# .../backend/src/geocaching_planner/devstack.py -> repository root
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PORT = 5432
DOCKER = shutil.which("docker") or "docker"


def check_preflight(
    *, docker_reachable: bool, port_free: bool, db_running: bool, port: int
) -> str | None:
    """Return a one-line actionable error, or None when the dev stack may start."""
    if not docker_reachable:
        return "Docker is not reachable: start Docker Desktop (or the Docker daemon) and retry."
    if not port_free and not db_running:
        return (
            f"DB_PORT {port} is already in use by another process: stop it, "
            "or set DB_PORT in .env to a free port and retry."
        )
    return None


def _docker_reachable() -> bool:
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no untrusted input
            [DOCKER, "info"], capture_output=True, check=False, timeout=15, cwd=REPO_ROOT
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def _port_free(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _db_running() -> bool:
    result = subprocess.run(  # noqa: S603 - fixed argv, no untrusted input
        [DOCKER, "compose", "ps", "--status", "running", "-q", "db"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def main(argv: Sequence[str] | None = None) -> None:
    port = int(os.environ.get("DB_PORT", DEFAULT_DB_PORT))
    docker_ok = _docker_reachable()
    error = check_preflight(
        docker_reachable=docker_ok,
        port_free=_port_free(port),
        db_running=docker_ok and _db_running(),
        port=port,
    )
    if error is not None:
        print(f"dev: {error}", file=sys.stderr)
        raise SystemExit(1)

    fetch = subprocess.run(  # noqa: S603 - fixed argv, no untrusted input
        ["/bin/sh", str(REPO_ROOT / "infra" / "brouter" / "fetch-release.sh")],
        check=False,
        cwd=REPO_ROOT,
    )
    if fetch.returncode != 0:
        print(
            "dev: could not fetch the BRouter release; check your network and retry.",
            file=sys.stderr,
        )
        raise SystemExit(fetch.returncode)

    up = subprocess.run(  # noqa: S603 - fixed argv, no untrusted input
        [DOCKER, "compose", "up", "-d", "--wait", "db", "brouter"], check=False, cwd=REPO_ROOT
    )
    if up.returncode != 0:
        print(
            "dev: the database or BRouter did not become healthy; "
            "see `docker compose logs db brouter`.",
            file=sys.stderr,
        )
        raise SystemExit(up.returncode)

    command.upgrade(alembic_config(AppConfig().database_url), "head")

    from geocaching_planner.__main__ import main as serve

    vite = _start_frontend()
    try:
        serve(["--reload"] if argv is None else list(argv))
    finally:
        _stop_frontend(vite)


def _start_frontend() -> subprocess.Popen[bytes]:
    """Start the Vite dev server (loopback, strict port) as a child of the dev stack."""
    vite = REPO_ROOT / "frontend" / "node_modules" / ".bin" / "vite"
    return subprocess.Popen([str(vite)], cwd=REPO_ROOT / "frontend")  # noqa: S603 - fixed argv


def _stop_frontend(vite: subprocess.Popen[bytes]) -> None:
    if vite.poll() is not None:
        return
    vite.terminate()
    try:
        vite.wait(timeout=10)
    except subprocess.TimeoutExpired:
        vite.kill()
        vite.wait()


if __name__ == "__main__":
    main()
