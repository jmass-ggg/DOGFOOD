"""Application configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        hide_input_in_errors=True,
    )
    
    # Application
    app_env: str = "development"
    app_name: str = "dogfood-api"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Logging
    log_level: str = "INFO"

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
    
    @property
    def is_development(self) -> bool:
        """Check if application is running in development mode."""
        return self.app_env == "development"


def get_settings() -> Settings:
    """Get settings instance (lazy loading)."""
    return Settings()
