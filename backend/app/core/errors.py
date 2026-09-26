"""Error handling infrastructure for the application.

This module provides:
- ApplicationError: Custom exception class for business logic errors
- Exception handlers for structured error responses
- Request ID inclusion in all error responses
"""

from typing import Any, Dict, Optional
import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse

from app.core.request_id import get_request_id


def error_response(request: Request, status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    request_id = request.scope.get("request_id") or get_request_id()
    return JSONResponse(
        status_code=status_code,
        headers={"X-Request-ID": request_id} if request_id else None,
        content={"error": {"code": code, "message": message, "details": details if details is not None else {}},
                 "request_id": request_id},
    )


class ApplicationError(Exception):
    """Custom exception for application-level errors.
    
    This exception should be raised for business logic errors, validation
    failures, and other expected error conditions. It provides structured
    error information with status codes.
    
    Attributes:
        code: Machine-readable error code (e.g., "INVALID_INPUT")
        message: Human-readable error message
        details: Optional dictionary with additional error context
        status_code: HTTP status code for the response
    """

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        """Initialize an ApplicationError.
        
        Args:
            code: Machine-readable error code
            message: Human-readable error message
            details: Optional dictionary with additional context
            status_code: HTTP status code (default: 400)
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


async def application_error_handler(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    """Handle ApplicationError exceptions with structured responses.
    
    Converts ApplicationError exceptions into JSON responses with:
    - error.code: Machine-readable error code
    - error.message: Human-readable message
    - error.details: Additional context
    - request_id: Request tracking ID
    
    Args:
        request: The FastAPI request object
        exc: The ApplicationError exception
        
    Returns:
        JSONResponse with structured error information
    """
    return error_response(request, exc.status_code, exc.code, exc.message, exc.details)


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unhandled exceptions with safe error responses.
    
    Catches any unhandled exception and returns a generic error response
    that doesn't expose internal details. The full exception is logged
    server-side for debugging.
    
    Args:
        request: The FastAPI request object
        exc: The unhandled exception
        
    Returns:
        JSONResponse with generic error information and 500 status
    """
    logging.getLogger("dogfood.errors").error("Unhandled exception type: %s", type(exc).__name__)
    return error_response(request, status.HTTP_500_INTERNAL_SERVER_ERROR,
                          "INTERNAL_ERROR", "An unexpected error occurred")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    response = error_response(request, exc.status_code, "HTTP_ERROR", message)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Input values in validation errors can contain credentials.
    return error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY,
                          "VALIDATION_ERROR", "Request validation failed")
