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

    APP_NAME: str
    APP_ENV: AppEnv = AppEnv.DEVELOPMENT
    DEBUG: bool = False

    SECRET_KEY: SecretStr = Field(repr=False)

    DATABASE_URL: SecretStr = Field(repr=False)

    FIREBASE_PROJECT_ID: str
    FIREBASE_SERVICE_ACCOUNT_JSON: SecretStr = Field(repr=False)

    GCS_BUCKET_NAME: str
    GCS_PROJECT_ID: str

    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    VCARD_BRANDING_NOTE: str = "Created with QR App · qrapp.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
