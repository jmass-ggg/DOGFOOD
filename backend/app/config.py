"""Application configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import Literal
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        hide_input_in_errors=True,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_name: str = "dogfood-api"

    # Database
    database_url: str

    # Logging
    log_level: str = "INFO"

    # JWT Authentication
    jwt_secret_key: str = Field(min_length=32, repr=False)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1, le=60)
    jwt_issuer: str = "dogfood-api"
    jwt_audience: str = "dogfood-api"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_signing_key(cls, value: str) -> str:
        if (
            len(value.strip()) < 32
            or value == "your-secret-key-here-change-in-production"
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be a generated secret of at least 32 characters"
            )
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            driver = make_url(value).drivername
        except ArgumentError:
            driver = None
        if driver != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value


def get_settings() -> Settings:
    """Get settings instance (lazy loading)."""
    return Settings()
