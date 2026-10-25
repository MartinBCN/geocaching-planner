import pytest

from geocaching_planner.devstack import check_preflight


def test_preflight_passes_when_docker_and_port_are_ready() -> None:
    assert (
        check_preflight(docker_reachable=True, port_free=True, db_running=False, port=5432) is None
    )


def test_preflight_fails_fast_when_docker_is_unreachable() -> None:
    message = check_preflight(docker_reachable=False, port_free=True, db_running=False, port=5432)

    assert message is not None
    assert "Docker" in message
    assert "start Docker" in message
    assert "\n" not in message


def test_preflight_fails_when_port_is_held_by_another_process() -> None:
    message = check_preflight(docker_reachable=True, port_free=False, db_running=False, port=6543)

    assert message is not None
    assert "DB_PORT 6543" in message
    assert "DB_PORT in .env" in message
    assert "\n" not in message


def test_preflight_accepts_port_held_by_this_projects_database() -> None:
    assert (
        check_preflight(docker_reachable=True, port_free=False, db_running=True, port=5432) is None
    )


@pytest.mark.parametrize("docker_reachable", [True, False])
def test_preflight_fails_fast_on_docker_or_port_error(docker_reachable: bool) -> None:
    message = check_preflight(
        docker_reachable=docker_reachable, port_free=False, db_running=False, port=5432
    )

    assert message is not None
