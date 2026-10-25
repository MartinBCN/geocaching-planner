import io
import json

import pytest
import structlog

from geocaching_planner.logging_config import configure_logging


def test_json_renderer_when_enabled() -> None:
    stream = io.StringIO()
    configure_logging(json_logs=True, stream=stream)

    structlog.get_logger("test").info("hello_event", thing=1)

    record = json.loads(stream.getvalue().strip().splitlines()[-1])
    assert record["event"] == "hello_event"
    assert record["level"] == "info"
    assert "timestamp" in record


def test_console_renderer_by_default() -> None:
    stream = io.StringIO()
    configure_logging(json_logs=False, stream=stream)

    structlog.get_logger("test").info("hello_event")

    output = stream.getvalue()
    assert "hello_event" in output
    with pytest.raises(json.JSONDecodeError):
        json.loads(output.strip().splitlines()[-1])
