from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────
    APP_NAME: str
    APP_ENV: AppEnv = AppEnv.DEVELOPMENT
    DEBUG: bool = False
    PUBLIC_BASE_URL: str
    SECRET_KEY: SecretStr = Field(repr=False)

    # ── Database ─────────────────────────────────────
    DATABASE_URL: SecretStr = Field(repr=False)

    # ── Firebase ─────────────────────────────────────
    FIREBASE_PROJECT_ID: str
    FIREBASE_SERVICE_ACCOUNT_JSON: SecretStr = Field(repr=False)

    # ── RevenueCat ───────────────────────────────────
    REVENUECAT_WEBHOOK_SECRET: SecretStr = Field(repr=False)

    # ── Google Cloud Storage ─────────────────────────
    GCS_BUCKET_NAME: str
    GCS_PROJECT_ID: str

    # ── CORS ─────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    # ── Pagination ───────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ── Branding ─────────────────────────────────────
    VCARD_BRANDING_NOTE: str = "Created with QR App · qrapp.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
