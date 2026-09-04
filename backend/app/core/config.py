from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    razorpay_key_id: str | None = Field(default=None, validation_alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: str | None = Field(default=None, validation_alias="RAZORPAY_KEY_SECRET")
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url_configured(self) -> bool:
        return bool(self.database_url and self.database_url.strip())

    def require_database_url(self) -> str:
        if not self.database_url_configured:
            raise RuntimeError("DATABASE_URL is required to connect to PostgreSQL.")
        return self.database_url.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
