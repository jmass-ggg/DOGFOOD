"""Unit tests for error handling infrastructure."""

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient

from app.core.errors import (
    ApplicationError,
    application_error_handler,
    generic_exception_handler,
)
from app.core.request_id import RequestIDMiddleware, request_id_context


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with error handlers."""
    app = FastAPI()
    
    # Define test routes
    async def test_app_error():
        raise ApplicationError(
            code="TEST_ERROR",
            message="This is a test error",
            details={"field": "value"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    
    async def test_app_error_404():
        raise ApplicationError(
            code="NOT_FOUND",
            message="Resource not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    async def test_generic_error():
        raise ValueError("Unexpected error")
    
    # Register routes
    app.get("/test-app-error")(test_app_error)
    app.get("/test-app-error-404")(test_app_error_404)
    app.get("/test-generic-error")(test_generic_error)
    
    # Add exception handlers
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Add request ID middleware
    app.add_middleware(RequestIDMiddleware)
    
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestApplicationError:
    """Tests for ApplicationError exception class."""
    
    def test_application_error_basic(self):
        """Test ApplicationError with basic parameters."""
        error = ApplicationError(
            code="TEST_CODE",
            message="Test message"
        )
        
        assert error.code == "TEST_CODE"
        assert error.message == "Test message"
        assert error.details == {}
        assert error.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_application_error_with_details(self):
        """Test ApplicationError with details."""
        details = {"field": "username", "reason": "too short"}
        error = ApplicationError(
            code="VALIDATION_ERROR",
            message="Validation failed",
            details=details
        )
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Validation failed"
        assert error.details == details
        assert error.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_application_error_custom_status_code(self):
        """Test ApplicationError with custom status code."""
        error = ApplicationError(
            code="NOT_FOUND",
            message="Resource not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
        
        assert error.status_code == status.HTTP_404_NOT_FOUND


class TestApplicationErrorHandler:
    """Tests for application_error_handler."""
    
    def test_application_error_response_format(self, client: TestClient):
        """Test ApplicationError returns structured JSON response."""
        response = client.get("/test-app-error")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "error" in data
        assert "request_id" in data
        
        error = data["error"]
        assert error["code"] == "TEST_ERROR"
        assert error["message"] == "This is a test error"
        assert error["details"] == {"field": "value"}
    
    def test_application_error_status_code(self, client: TestClient):
        """Test ApplicationError respects custom status codes."""
        response = client.get("/test-app-error-404")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert data["error"]["message"] == "Resource not found"
    
    def test_application_error_includes_request_id(self, client: TestClient):
        """Test ApplicationError response includes request ID."""
        # Send request with custom request ID
        response = client.get(
            "/test-app-error",
            headers={"X-Request-ID": "test-request-123"}
        )
        
        data = response.json()
        assert data["request_id"] == "test-request-123"
    
    def test_application_error_generates_request_id(self, client: TestClient):
        """Test ApplicationError generates request ID when not provided."""
        response = client.get("/test-app-error")
        
        data = response.json()
        assert "request_id" in data
        assert len(data["request_id"]) > 0
        # Should be a UUID format
        assert "-" in data["request_id"]


class TestGenericExceptionHandler:
    """Tests for generic_exception_handler."""
    
    def test_generic_exception_returns_500(self, client: TestClient):
        """Test unhandled exceptions return 500 status."""
        response = client.get("/test-generic-error")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_generic_exception_response_format(self, client: TestClient):
        """Test unhandled exceptions return structured response."""
        response = client.get("/test-generic-error")
        
        data = response.json()
        assert "error" in data
        assert "request_id" in data
        
        error = data["error"]
        assert error["code"] == "INTERNAL_ERROR"
        assert error["message"] == "An unexpected error occurred"
        assert error["details"] == {}
    
    def test_generic_exception_includes_request_id(self, client: TestClient):
        """Test generic exception includes request ID."""
        response = client.get(
            "/test-generic-error",
            headers={"X-Request-ID": "error-request-456"}
        )
        
        data = response.json()
        assert data["request_id"] == "error-request-456"
    
    def test_generic_exception_no_stack_trace(self, client: TestClient):
        """Test generic exception doesn't expose stack trace."""
        response = client.get("/test-generic-error")
        
        data = response.json()
        response_text = response.text
        
        # Should not contain Python stack trace elements
        assert "Traceback" not in response_text
        assert "ValueError" not in response_text
        assert "Unexpected error" not in response_text  # Original error message
