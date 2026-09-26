"""Error handling infrastructure for the application.

This module provides:
- ApplicationError: Custom exception class for business logic errors
- Exception handlers for structured error responses
- Request ID inclusion in all error responses
"""

from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.request_id import get_request_id


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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": get_request_id(),
        },
    )


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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
            "request_id": get_request_id(),
        },
    )
