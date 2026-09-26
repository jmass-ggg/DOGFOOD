"""Application configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
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
    
    @property
    def is_development(self) -> bool:
        """Check if application is running in development mode."""
        return self.app_env == "development"


def get_settings() -> Settings:
    """Get settings instance (lazy loading)."""
    return Settings()

