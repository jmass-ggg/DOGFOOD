"""Logging infrastructure with request context and structured formatting."""

import logging
import sys
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
    logging.basicConfig(
        level=log_level.upper(),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Add request ID filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(RequestIDFilter())
    
    # Quiet noisy libraries to reduce log volume
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

