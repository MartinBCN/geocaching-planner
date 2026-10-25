from pathlib import Path

from alembic.config import Config

from geocaching_planner.config import AppConfig

# .../backend/src/geocaching_planner/adapters/db/migrations.py -> .../backend
BACKEND_DIR = Path(__file__).resolve().parents[4]


def alembic_config(database_url: str | None = None) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.attributes["database_url"] = database_url or AppConfig().database_url
    return config
