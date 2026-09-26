"""Clock abstraction for timezone-aware UTC timestamps."""

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Protocol for clock implementations."""
    
    def now(self) -> datetime:
        """Return current UTC time with timezone awareness."""
        ...


class UTCClock:
    """Clock implementation that returns timezone-aware UTC timestamps."""
    
    def now(self) -> datetime:
        """Return current UTC time with timezone awareness.
        
        Returns:
            datetime: Current UTC time with timezone information.
        """
        return datetime.now(timezone.utc)


# Default clock instance
clock = UTCClock()
