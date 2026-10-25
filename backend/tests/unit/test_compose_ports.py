from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.compose_ports import find_non_loopback_ports

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("ports", "expected_violations"),
    [
        (["127.0.0.1:5432:5432"], 0),
        (["127.0.0.1:${DB_PORT:-5432}:5432"], 0),
        (["5432:5432"], 1),
        (["0.0.0.0:5432:5432"], 1),
        (["5432"], 1),
        (["[::1]:5432:5432"], 1),
        (["localhost:5432:5432"], 1),
        (["127.0.0.1:5432:5432/tcp"], 0),
        ([{"target": 5432, "published": 5432, "host_ip": "127.0.0.1"}], 0),
        ([{"target": 5432, "published": 5432}], 1),
        ([{"target": 5432, "published": 5432, "host_ip": "0.0.0.0"}], 1),  # noqa: S104 - test data for a rejected bind address
    ],
)
def test_port_binding_validation(ports: list[Any], expected_violations: int) -> None:
    compose = {"services": {"db": {"ports": ports}}}

    assert len(find_non_loopback_ports(compose)) == expected_violations


def test_services_without_published_ports_are_allowed() -> None:
    compose = {"services": {"api": {"expose": ["8000"]}, "worker": {}}}

    assert find_non_loopback_ports(compose) == []


def test_repository_compose_file_publishes_only_on_loopback() -> None:
    compose = yaml.safe_load((REPO_ROOT / "compose.yaml").read_text())

    assert find_non_loopback_ports(compose) == []
