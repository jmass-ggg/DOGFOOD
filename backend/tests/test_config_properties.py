"""Property-based tests for configuration management."""

import os
from hypothesis import given, strategies as st
from app.config import Settings


@given(
    database_url=st.just("postgresql+psycopg://test:test@localhost/testdb"),
    app_env=st.text(min_size=1),
    app_name=st.text(min_size=1),
    api_v1_prefix=st.text(min_size=1),
    frontend_url=st.text(min_size=1),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def test_property_configuration_loading(
    database_url: str,
    app_env: str,
    app_name: str,
    api_v1_prefix: str,
    frontend_url: str,
    log_level: str,
):
    """
    Feature: backend-foundation, Property 1: Configuration Loading
    
    For any valid environment variable with a corresponding configuration field,
    setting that environment variable should result in the configuration object
    containing that value.
    
    Validates: Requirements 1.1
    """
    # Create settings with generated values
    settings = Settings(
        database_url=database_url,
        app_env=app_env,
        app_name=app_name,
        api_v1_prefix=api_v1_prefix,
        frontend_url=frontend_url,
        log_level=log_level,
    )
    
    # Verify that each field contains the value we set
    assert settings.database_url == database_url
    assert settings.app_env == app_env
    assert settings.app_name == app_name
    assert settings.api_v1_prefix == api_v1_prefix
    assert settings.frontend_url == frontend_url
    assert settings.log_level == log_level
