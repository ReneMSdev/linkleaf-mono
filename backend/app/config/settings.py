from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
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
    # Firebase UIDs allowed to use the API. Empty = no restriction (local/test only);
    # staging and production refuse to start without it. JSON list in env:
    # ALLOWED_FIREBASE_UIDS=["uid1","uid2"]
    ALLOWED_FIREBASE_UIDS: list[str] = Field(default_factory=list)

    # ── RevenueCat ───────────────────────────────────
    REVENUECAT_WEBHOOK_SECRET: SecretStr = Field(repr=False)

    # ── Google Cloud Storage ─────────────────────────
    GCS_PUBLIC_BUCKET_NAME: str   # images and avatars — publicly readable
    GCS_PRIVATE_BUCKET_NAME: str  # resumes — private, signed URLs only
    GCS_PROJECT_ID: str
    GCS_SERVICE_ACCOUNT_JSON: SecretStr = Field(repr=False)

    # ── CORS ─────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    # ── Pagination ───────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ── Branding ─────────────────────────────────────
    VCARD_BRANDING_NOTE: str = "Created with LinkLeaf · linkleaf.co"

    @model_validator(mode="after")
    def _require_uid_allowlist_when_deployed(self) -> "Settings":
        if (
            self.APP_ENV in (AppEnv.STAGING, AppEnv.PRODUCTION)
            and not self.ALLOWED_FIREBASE_UIDS
        ):
            raise ValueError(
                "ALLOWED_FIREBASE_UIDS must be set in staging and production."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
