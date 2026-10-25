import pytest

from geocaching_planner.config import AppConfig


def test_config_defaults_and_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = AppConfig(_env_file=None)
    assert (defaults.host, defaults.port, defaults.log_json) == ("127.0.0.1", 8000, False)

    monkeypatch.setenv("GCP_PORT", "9000")
    monkeypatch.setenv("GCP_LOG_JSON", "true")
    overridden = AppConfig(_env_file=None)
    assert overridden.port == 9000
    assert overridden.log_json is True
