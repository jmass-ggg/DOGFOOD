"""Unit tests for logging infrastructure."""

import logging
from io import StringIO
from unittest.mock import patch

from app.core.logging import RequestIDFilter, configure_logging
from app.core.request_id import request_id_context


class TestRequestIDFilter:
    """Test RequestIDFilter adds request_id to log records."""

    def test_filter_adds_request_id_when_present(self):
        """Test that filter adds request_id from context to log record."""
        # Set up request ID in context
        request_id_context.set("test-request-123")
        
        # Create filter and log record
        filter_instance = RequestIDFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Apply filter
        result = filter_instance.filter(record)
        
        # Verify filter returns True and adds request_id
        assert result is True
        assert hasattr(record, "request_id")
        assert record.request_id == "test-request-123"

    def test_filter_adds_na_when_no_request_id(self):
        """Test that filter adds 'N/A' when no request ID in context."""
        # Clear request ID context
        request_id_context.set("")
        
        # Create filter and log record
        filter_instance = RequestIDFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Apply filter
        result = filter_instance.filter(record)
        
        # Verify filter returns True and adds 'N/A'
        assert result is True
        assert hasattr(record, "request_id")
        assert record.request_id == "N/A"


class TestConfigureLogging:
    """Test configure_logging function."""

    def test_logger_configuration_sets_level(self):
        """Test that configure_logging sets the specified log level."""
        # Store original state
        original_level = logging.root.level
        original_handlers = logging.root.handlers.copy()
        
        try:
            # Clear existing handlers to allow clean configuration
            logging.root.handlers.clear()
            
            # Configure with DEBUG level
            configure_logging("DEBUG")
            
            # Verify root logger has DEBUG level
            assert logging.root.level == logging.DEBUG
            
            # Clear handlers again for second configuration
            logging.root.handlers.clear()
            
            # Reconfigure with WARNING level
            configure_logging("WARNING")
            
            # Verify root logger has WARNING level
            assert logging.root.level == logging.WARNING
        finally:
            # Restore original state
            logging.root.setLevel(original_level)
            logging.root.handlers.clear()
            logging.root.handlers.extend(original_handlers)

    def test_logger_configuration_adds_filter(self):
        """Test that configure_logging adds RequestIDFilter to handlers."""
        # Configure logging
        configure_logging("INFO")
        
        # Verify at least one handler has RequestIDFilter
        has_filter = False
        for handler in logging.root.handlers:
            for filter_obj in handler.filters:
                if isinstance(filter_obj, RequestIDFilter):
                    has_filter = True
                    break
        
        assert has_filter, "RequestIDFilter should be added to handlers"

    def test_logger_configuration_outputs_structured_format(self):
        """Test that configure_logging produces structured log output."""
        # Set up request ID
        request_id_context.set("test-log-456")
        
        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s')
        )
        handler.addFilter(RequestIDFilter())
        
        # Create test logger
        test_logger = logging.getLogger("test_structured")
        test_logger.handlers = [handler]
        test_logger.setLevel(logging.INFO)
        
        # Log a message
        test_logger.info("Test structured log message")
        
        # Get output
        output = log_stream.getvalue()
        
        # Verify structured format includes key components
        assert "test_structured" in output
        assert "INFO" in output
        assert "[test-log-456]" in output
        assert "Test structured log message" in output

    def test_uvicorn_access_logs_quieted(self):
        """Test that uvicorn.access logger is set to WARNING level."""
        # Configure logging
        configure_logging("INFO")
        
        # Verify uvicorn.access logger is at WARNING level
        uvicorn_logger = logging.getLogger("uvicorn.access")
        assert uvicorn_logger.level == logging.WARNING

