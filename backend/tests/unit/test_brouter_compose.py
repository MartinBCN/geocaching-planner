import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE = REPO_ROOT / "compose.yaml"
INFRA = REPO_ROOT / "infra" / "brouter"
ENTRYPOINT_MESSAGE = "No routing data found — run `mise run brouter:segments`"


def _brouter_service() -> dict[str, object]:
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    service: dict[str, object] = compose["services"]["brouter"]
    return service


def test_service_starts_without_segments_and_binds_loopback() -> None:
    """AC1/AC5: brouter has a healthcheck, read-only data mounts, and a loopback-only port."""
    service = _brouter_service()

    assert service["build"] == {"context": "./infra/brouter"}
    ports = service["ports"]
    assert isinstance(ports, list)
    assert ports == ["127.0.0.1:${BROUTER_PORT:-17777}:17777"]

    volumes = service["volumes"]
    assert isinstance(volumes, list)
    assert "./infra/brouter/segments:/data/segments:ro" in volumes
    assert "./infra/brouter/profiles:/data/profiles:ro" in volumes

    healthcheck = service["healthcheck"]
    assert isinstance(healthcheck, dict)
    assert "curl" in str(healthcheck["test"])


def test_entrypoint_reports_missing_routing_data_without_failing() -> None:
    entrypoint = (INFRA / "entrypoint.sh").read_text(encoding="utf-8")

    assert ENTRYPOINT_MESSAGE in entrypoint
    assert "exec java" in entrypoint
    # Warn only: the server must still start without segments.
    assert "exit 1" not in entrypoint


def test_release_version_and_checksum_match_between_script_and_dockerfile() -> None:
    script = (INFRA / "fetch-release.sh").read_text(encoding="utf-8")
    dockerfile = (INFRA / "Dockerfile").read_text(encoding="utf-8")

    def value(text: str, name: str) -> str:
        match = re.search(rf"^(?:ARG )?{name}=(\S+)$", text, re.MULTILINE)
        assert match, f"{name} not found"
        return match.group(1)

    assert value(script, "BROUTER_VERSION") == value(dockerfile, "BROUTER_VERSION")
    assert value(script, "BROUTER_ZIP_SHA256") == value(dockerfile, "BROUTER_ZIP_SHA256")


@pytest.mark.parametrize("line", ["infra/brouter/segments/*", "!infra/brouter/segments/.gitkeep"])
def test_segment_data_is_git_ignored(line: str) -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert line in gitignore


def test_release_cache_is_git_ignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "infra/brouter/.cache/" in gitignore
