"""Logging infrastructure with request context and structured formatting."""

import logging
import json
import sys
from datetime import datetime, timezone
from app.core.request_id import get_request_id


class RequestIDFilter(logging.Filter):
    """Logging filter that adds request_id to log records.
    
    This filter adds the current request ID from the request context
    to every log record, allowing request tracing through logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id attribute to log record.
        
        Args:
            record: The log record to filter
            
        Returns:
            Always True to include the record in output
        """
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id() or "N/A"
        return True


def configure_logging(log_level: str) -> None:
    """Configure application logging with structured format and request context.
    
    Sets up logging with:
    - Configurable log level from settings
    - Structured log format including timestamp, logger name, level, request_id, and message
    - Request ID filter for all handlers
    - Console output to stdout
    - Quieted uvicorn access logs to reduce noise
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure root logger
    default_handler = logging.StreamHandler(sys.stdout)
    default_handler.setFormatter(JSONLogFormatter())
    logging.basicConfig(level=log_level.upper(), handlers=[default_handler])
    logging.root.setLevel(log_level.upper())
    
    # Add request ID filter to all handlers
    for handler in logging.root.handlers:
        if not any(isinstance(f, RequestIDFilter) for f in handler.filters):
            handler.addFilter(RequestIDFilter())

    request_logger = logging.getLogger("dogfood.request")
    request_logger.setLevel(log_level.upper())
    request_logger.propagate = False
    if not request_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(RequestIDFilter())
        handler.setFormatter(JSONLogFormatter())
        request_logger.addHandler(handler)
    
    # Quiet noisy libraries to reduce log volume
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class JSONLogFormatter(logging.Formatter):
    """Emit request logs as one JSON object per line without query strings."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "N/A"),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
        })
