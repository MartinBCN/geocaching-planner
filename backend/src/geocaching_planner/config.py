from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Runtime settings. Every field is read from a `GCP_`-prefixed environment variable."""

    model_config = SettingsConfigDict(env_prefix="GCP_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8000
    log_json: bool = False
    tile_url: str = "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png"
    tile_attribution: str = "© OpenStreetMap contributors, CyclOSM"
    # Local development default; matches the compose PostGIS service defaults (compose.yaml).
    database_url: str = "postgresql+asyncpg://geocaching:geocaching@127.0.0.1:5432/geocaching"
