import socket
import subprocess
from types import SimpleNamespace
from typing import Any, cast

import pytest
from alembic import command

import geocaching_planner.__main__ as entry
from geocaching_planner import devstack
from geocaching_planner.api.deps import get_session


def _completed(returncode: int, stdout: str = "") -> Any:
    return SimpleNamespace(returncode=returncode, stdout=stdout)


@pytest.fixture
def vite_events() -> list[str]:
    """Start and stop events recorded by the fake Vite process."""
    return []


@pytest.fixture(autouse=True)
def _no_real_vite(monkeypatch: pytest.MonkeyPatch, vite_events: list[str]) -> None:
    """Keep unit tests from launching Vite; the fake process records start and stop events."""
    events = vite_events

    class FakeVite:
        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            events.append("stop")

        def wait(self, timeout: float | None = None) -> int:
            return 0

    def _start() -> Any:
        events.append("start")
        return FakeVite()

    monkeypatch.setattr(devstack, "_start_frontend", _start)


def test_main_runs_vite_alongside_the_backend_and_stops_it_afterwards(
    monkeypatch: pytest.MonkeyPatch, vite_events: list[str]
) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: True)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    monkeypatch.setattr(devstack, "_db_running", lambda: False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0))
    monkeypatch.setattr(command, "upgrade", lambda _cfg, _rev: None)

    def _serve(_argv: list[str]) -> None:
        vite_events.append("serve")

    monkeypatch.setattr(entry, "main", _serve)

    devstack.main([])

    assert vite_events == ["start", "serve", "stop"]


def test_main_stops_vite_even_when_the_backend_fails(
    monkeypatch: pytest.MonkeyPatch, vite_events: list[str]
) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: True)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    monkeypatch.setattr(devstack, "_db_running", lambda: False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0))
    monkeypatch.setattr(command, "upgrade", lambda _cfg, _rev: None)

    def _boom(_argv: list[str]) -> None:
        raise RuntimeError("backend crashed")

    monkeypatch.setattr(entry, "main", _boom)

    with pytest.raises(RuntimeError, match="backend crashed"):
        devstack.main([])

    assert vite_events == ["start", "stop"]


def test_stop_frontend_terminates_a_running_vite_and_kills_it_when_it_hangs() -> None:
    class Hung:
        def __init__(self) -> None:
            self.terminated = False
            self.killed = False

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: float | None = None) -> int:
            if not self.killed:
                raise subprocess.TimeoutExpired(cmd="vite", timeout=timeout or 0)
            return 0

        def kill(self) -> None:
            self.killed = True

    hung = Hung()
    devstack._stop_frontend(cast("subprocess.Popen[bytes]", hung))
    assert hung.terminated
    assert hung.killed


def test_docker_reachable_is_false_when_docker_binary_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _missing(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError("docker")

    monkeypatch.setattr(subprocess, "run", _missing)
    assert devstack._docker_reachable() is False


def test_docker_reachable_follows_docker_info_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0))
    assert devstack._docker_reachable() is True

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(1))
    assert devstack._docker_reachable() is False


def test_db_running_requires_a_container_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0, "abc123\n"))
    assert devstack._db_running() is True

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0, ""))
    assert devstack._db_running() is False


@pytest.mark.enable_socket
def test_port_free_detects_a_listener() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        assert devstack._port_free(port) is False

    assert devstack._port_free(port) is True


def test_main_exits_before_starting_anything_when_preflight_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: False)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    calls: list[object] = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append(a))

    with pytest.raises(SystemExit) as excinfo:
        devstack.main([])

    assert excinfo.value.code == 1
    assert calls == []


def test_main_starts_database_migrates_and_serves(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: True)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    monkeypatch.setattr(devstack, "_db_running", lambda: False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0))
    upgrades: list[str] = []
    monkeypatch.setattr(command, "upgrade", lambda _cfg, rev: upgrades.append(rev))
    served: list[list[str]] = []
    monkeypatch.setattr(entry, "main", lambda argv: served.append(list(argv)))

    devstack.main(["--reload"])

    assert upgrades == ["head"]
    assert served == [["--reload"]]


def test_main_fetches_brouter_release_and_starts_db_and_brouter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: True)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    monkeypatch.setattr(devstack, "_db_running", lambda: False)
    calls: list[list[str]] = []

    def _record(argv: list[str], **_kwargs: object) -> Any:
        calls.append(list(argv))
        return _completed(0)

    monkeypatch.setattr(subprocess, "run", _record)
    monkeypatch.setattr(command, "upgrade", lambda _cfg, _rev: None)
    monkeypatch.setattr(entry, "main", lambda _argv: None)

    devstack.main([])

    fetch = [c for c in calls if c[-1].endswith("fetch-release.sh")]
    up = [c for c in calls if "compose" in c and "up" in c]
    assert fetch, "BRouter release is not fetched before compose up"
    assert calls.index(fetch[0]) < calls.index(up[0])
    assert up[0][-3:] == ["--wait", "db", "brouter"]


def test_main_stops_when_brouter_release_fetch_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: True)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    monkeypatch.setattr(devstack, "_db_running", lambda: False)
    calls: list[list[str]] = []

    def _fail_fetch(argv: list[str], **_kwargs: object) -> Any:
        calls.append(list(argv))
        return _completed(7 if argv[-1].endswith("fetch-release.sh") else 0)

    monkeypatch.setattr(subprocess, "run", _fail_fetch)

    with pytest.raises(SystemExit) as excinfo:
        devstack.main([])

    assert excinfo.value.code == 7
    assert not any("compose" in c for c in calls)


def test_main_stops_when_compose_up_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(devstack, "_docker_reachable", lambda: True)
    monkeypatch.setattr(devstack, "_port_free", lambda _port: True)
    monkeypatch.setattr(devstack, "_db_running", lambda: False)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(3))

    with pytest.raises(SystemExit) as excinfo:
        devstack.main([])

    assert excinfo.value.code == 3


async def test_get_session_yields_a_session_from_app_state() -> None:
    entered: list[str] = []

    class FakeSession:
        async def __aenter__(self) -> FakeSession:
            entered.append("enter")
            return self

        async def __aexit__(self, *_exc: object) -> None:
            entered.append("exit")

    request: Any = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(session_factory=lambda: FakeSession()))
    )
    sessions = [session async for session in get_session(request)]
    assert len(sessions) == 1
    assert isinstance(sessions[0], FakeSession)
    assert entered == ["enter", "exit"]
