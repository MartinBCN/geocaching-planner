import importlib

import pytest


@pytest.mark.parametrize(
    "module", ["fastapi", "uvicorn", "pydantic_settings", "structlog", "pydantic", "httpx"]
)
def test_runtime_imports(module: str) -> None:
    importlib.import_module(module)


def test_database_dependencies_import() -> None:
    for module in ("sqlalchemy", "asyncpg", "geoalchemy2", "alembic"):
        importlib.import_module(module)
