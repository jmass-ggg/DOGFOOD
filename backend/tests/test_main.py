"""Unit tests for application initialization."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.main import create_app, app
from app.core.request_id import RequestIDMiddleware
from app.core.errors import ApplicationError


def test_fastapi_app_creation():
    """
    Test that create_app() creates a FastAPI instance.
    
    Requirements: 2.1 - Application starts and creates FastAPI instance
    """
    test_app = create_app()
    
    # Verify it's a FastAPI instance
    assert isinstance(test_app, FastAPI)
    
    # Verify basic configuration
    assert test_app.title == "dogfood-api"
    assert test_app.version == "1.0.0"


def test_middleware_installation():
    """
    Test that RequestIDMiddleware is installed.
    
    Requirements: 2.3 - Application installs request-ID middleware
    """
    test_app = create_app()
    
    # Check that middleware is installed
    # FastAPI stores middleware in app.user_middleware
    middleware_classes = [m.cls for m in test_app.user_middleware]
    
    assert RequestIDMiddleware in middleware_classes


def test_exception_handler_registration():
    """
    Test that exception handlers are registered.
    
    Requirements: 2.4 - Application installs reusable exception handling
    """
    test_app = create_app()
    
    # Check that exception handlers are registered
    assert ApplicationError in test_app.exception_handlers
    assert Exception in test_app.exception_handlers


def test_router_inclusion():
    """
    Test that health router is included.
    
    Requirements: 2.5 - Application exposes health endpoint
    """
    test_app = create_app()
    
    # Check the public API contract rather than FastAPI's internal route classes.
    assert "/health" in test_app.openapi()["paths"]


@pytest.mark.asyncio
async def test_middleware_functions():
    """
    Test that middleware actually works in request flow.
    
    Requirements: 2.3 - Request ID middleware is functional
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    
    # Verify request ID is added to response
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


@pytest.mark.asyncio
async def test_exception_handlers_work():
    """
    Test that exception handlers catch errors properly.
    
    Requirements: 2.4 - Exception handlers are functional
    """
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    
    # Create a separate test app for this test
    test_app = create_app()
    
    # Add a test route that raises ApplicationError
    @test_app.get("/test-error")
    async def test_error_route():
        raise ApplicationError(
            code="TEST_ERROR",
            message="This is a test error",
            status_code=400
        )
    
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/test-error")
    
    # Verify error response structure
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "TEST_ERROR"
    assert data["error"]["message"] == "This is a test error"
    assert "request_id" in data


@pytest.mark.asyncio
async def test_logging_configured():
    """
    Test that logging is configured during app creation.
    
    Requirements: 2.2 - Application configures logging infrastructure
    """
    import logging
    
    # Create a new app instance to trigger logging configuration
    test_app = create_app()
    
    # Verify root logger has handlers
    assert len(logging.root.handlers) > 0
    
    # Verify log level is set (should be INFO by default)
    # Note: The actual level depends on environment configuration
    assert logging.root.level in [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL
    ]
