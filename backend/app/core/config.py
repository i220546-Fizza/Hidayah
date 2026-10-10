from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (and backend/.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field(default="development", description="development | test | production")
    database_url: str = Field(
        default="postgresql+psycopg://hidayah:change-me@localhost:5432/hidayah",
        description="SQLAlchemy URL. Never commit real credentials.",
    )
    secret_key: str = Field(default="dev-only-not-secret", description="Signing key (Phase 4)")
    allowed_origins: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of origins allowed by CORS.",
    )
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
