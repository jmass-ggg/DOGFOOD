"""Unit tests for clock abstraction."""

from datetime import datetime, timezone
from app.core.clock import Clock, UTCClock, clock


def test_utc_clock_returns_datetime():
    """Test that UTCClock.now() returns a datetime object."""
    utc_clock = UTCClock()
    result = utc_clock.now()
    
    assert isinstance(result, datetime)


def test_utc_clock_timezone_awareness():
    """Test that UTCClock.now() returns timezone-aware UTC datetime."""
    utc_clock = UTCClock()
    result = utc_clock.now()
    
    # Check timezone awareness
    assert result.tzinfo is not None, "Datetime should be timezone-aware"
    assert result.tzinfo == timezone.utc, "Datetime should have UTC timezone"


def test_default_clock_instance():
    """Test that the default clock instance works correctly."""
    result = clock.now()
    
    assert isinstance(result, datetime)
    assert result.tzinfo == timezone.utc


def test_clock_protocol_compliance():
    """Test that UTCClock implements the Clock protocol."""
    utc_clock = UTCClock()
    
    # Verify it has the now() method
    assert hasattr(utc_clock, 'now')
    assert callable(utc_clock.now)
    
    # Verify it can be used as a Clock
    def accepts_clock(c: Clock) -> datetime:
        return c.now()
    
    result = accepts_clock(utc_clock)
    assert isinstance(result, datetime)
