"""Unit tests for configuration management."""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError
from app.config import Settings


def test_required_settings_present(monkeypatch, tmp_path):
    """Test that required settings must be provided."""
    # DATABASE_URL is required and has no default
    # Clear environment variable to test validation
    monkeypatch.delenv("DATABASE_URL", raising=False)
    
    # Point to non-existent .env file to prevent loading from actual .env
    monkeypatch.chdir(tmp_path)
    
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="test",
            app_name="test-api",
            # Missing DATABASE_URL
        )
    
    errors = exc_info.value.errors()
    assert any(error["loc"] == ("database_url",) for error in errors)


def test_default_values_applied():
    """Test that optional settings have correct defaults."""
    settings = Settings(database_url="postgresql+psycopg://test:test@localhost/test")
    
    # Check default values
    assert settings.app_env == "development"
    assert settings.app_name == "dogfood-api"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.frontend_url == "http://localhost:3000"
    assert settings.log_level == "INFO"


def test_custom_values_override_defaults():
    """Test that provided values override defaults."""
    settings = Settings(
        database_url="postgresql+psycopg://custom:custom@localhost/custom",
        app_env="production",
        app_name="custom-api",
        api_v1_prefix="/api/v2",
        frontend_url="https://example.com",
        log_level="DEBUG"
    )
    
    assert settings.app_env == "production"
    assert settings.app_name == "custom-api"
    assert settings.api_v1_prefix == "/api/v2"
    assert settings.frontend_url == "https://example.com"
    assert settings.log_level == "DEBUG"


def test_is_development_property():
    """Test the is_development property."""
    dev_settings = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        app_env="development"
    )
    assert dev_settings.is_development is True
    
    prod_settings = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        app_env="production"
    )
    assert prod_settings.is_development is False


def test_env_example_contains_no_secrets():
    """Test that .env.example file contains only placeholder values, not real secrets."""
    env_example_path = Path(__file__).parent.parent / ".env.example"
    
    assert env_example_path.exists(), ".env.example file should exist"
    
    content = env_example_path.read_text()
    
    # Check for patterns that indicate real secrets (not exhaustive, but catches common issues)
    forbidden_patterns = [
        "sk_live_",  # Stripe live keys
        "sk_test_",  # Stripe test keys (still sensitive)
        "-----BEGIN",  # Private keys
        "ghp_",  # GitHub personal access tokens
        "gho_",  # GitHub OAuth tokens
        "xoxb-",  # Slack bot tokens
        "xoxp-",  # Slack user tokens
    ]
    
    for pattern in forbidden_patterns:
        assert pattern not in content, f".env.example should not contain pattern '{pattern}'"
    
    # Check that it contains expected configuration keys
    assert "DATABASE_URL" in content
    assert "APP_ENV" in content
    assert "APP_NAME" in content
    assert "FRONTEND_URL" in content
    assert "LOG_LEVEL" in content
