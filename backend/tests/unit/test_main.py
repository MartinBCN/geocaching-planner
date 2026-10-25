from typing import Any

import pytest
import uvicorn

from geocaching_planner.__main__ import main


def test_entry_point_uses_configured_bind(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}

    def fake_run(app: str, **kwargs: Any) -> None:
        calls["app"] = app
        calls.update(kwargs)

    monkeypatch.setattr(uvicorn, "run", fake_run)
    monkeypatch.setenv("GCP_PORT", "9000")

    main([])
    assert calls["app"] == "geocaching_planner.main:create_app"
    assert calls["factory"] is True
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 9000
    assert calls["reload"] is False

    main(["--reload"])
    assert calls["reload"] is True
