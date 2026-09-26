"""Request ID middleware for tracking requests through the system."""

import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable to store request ID for the current request
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that manages request ID tracking.
    
    - Extracts X-Request-ID from request headers if present
    - Generates a new UUID if not present
    - Stores request ID in context variable for access during request processing
    - Adds X-Request-ID to response headers
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in context variable for access during request processing
        request_id_context.set(request_id)
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id() -> str:
    """Get the current request ID from context.
    
    Returns:
        The request ID for the current request, or empty string if not set.
    """
    return request_id_context.get()
