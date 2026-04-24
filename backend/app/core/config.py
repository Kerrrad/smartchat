from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{(BASE_DIR / 'smartchat.db').as_posix()}"


class Settings(BaseSettings):
    app_name: str = "SmartChat Automation"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field("dev-secret-change-me-please", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = DEFAULT_SQLITE_URL
    redis_url: str = "redis://localhost:6379/0"
    enable_celery_dispatch: bool = False
    allow_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    log_level: str = "INFO"
    app_timezone: str = "Europe/Warsaw"
    default_admin_email: str = "admin@smartchat.local"
    default_admin_password: str = "Admin123!"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allow_origins.split(",") if origin.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("sqlite+aiosqlite:///"):
            return self.database_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
        return self.database_url

    def public_settings(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "environment": self.app_env,
            "debug": self.app_debug,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
