"""Request ID middleware for tracking requests through the system."""

import uuid
import logging
import time
import re
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
        if not request_id or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
            request_id = str(uuid.uuid4())
        
        # Store in context variable for access during request processing
        request.scope["request_id"] = request_id
        token = request_id_context.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            logging.getLogger("dogfood.request").info(
                "request", extra={
                    "method": request.method,
                    "path": getattr(request.scope.get("route"), "path", "<unmatched>"),
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            request_id_context.reset(token)


def get_request_id() -> str:
    """Get the current request ID from context.
    
    Returns:
        The request ID for the current request, or empty string if not set.
    """
    return request_id_context.get()
