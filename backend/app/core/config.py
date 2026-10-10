from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Only for local development and tests. Production refuses to start with this value.
DEV_SECRET = "dev-only-secret-not-for-production-0123456789"


class Settings(BaseSettings):
    """Application settings, read from environment variables (and backend/.env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = Field(default="development", description="development | test | production")
    database_url: str = Field(
        default="postgresql+psycopg://hidayah:change-me@localhost:5432/hidayah",
        description="SQLAlchemy URL. Never commit real credentials.",
    )
    secret_key: str = Field(default=DEV_SECRET, description="Signing key for access tokens")
    allowed_origins: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of origins allowed by CORS.",
    )
    log_level: str = "INFO"

    # --- Authentication ---
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    # Refresh cookie is Secure (HTTPS only) everywhere except local development.
    cookie_secure: bool | None = None
    login_rate_limit: int = 10  # attempts per window per client+email
    rate_limit_window_seconds: int = 300

    @property
    def secure_cookies(self) -> bool:
        return self.cookie_secure if self.cookie_secure is not None else self.env == "production"

    @model_validator(mode="after")
    def _require_real_secret_in_production(self) -> "Settings":
        if self.env == "production" and (
            self.secret_key == DEV_SECRET or len(self.secret_key) < 32
        ):
            raise ValueError("SECRET_KEY must be set to a random value of 32+ characters in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
