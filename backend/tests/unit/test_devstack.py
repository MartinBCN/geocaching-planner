import socket
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest
from alembic import command

import geocaching_planner.__main__ as entry
from geocaching_planner import devstack
from geocaching_planner.api.deps import get_session


def _completed(returncode: int, stdout: str = "") -> Any:
    return SimpleNamespace(returncode=returncode, stdout=stdout)


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
