import importlib

import pytest


@pytest.mark.parametrize(
    "module", ["fastapi", "uvicorn", "pydantic_settings", "structlog", "pydantic", "httpx"]
)
def test_runtime_imports(module: str) -> None:
    importlib.import_module(module)
