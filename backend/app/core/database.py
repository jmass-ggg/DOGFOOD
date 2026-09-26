"""Database layer with SQLAlchemy 2.x async support."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.models import Base

# Re-export Base for convenience
__all__ = ["Base", "create_engine", "create_session_factory", "get_db_session", "engine", "session_factory"]


def create_engine(database_url: str) -> AsyncEngine:
    """
    Create async SQLAlchemy engine for PostgreSQL.
    
    Args:
        database_url: PostgreSQL connection string (must use postgresql+asyncpg://)
    
    Returns:
        Configured AsyncEngine instance
    """
    return create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using them
        pool_size=5,         # Connection pool size
        max_overflow=10      # Additional connections beyond pool_size
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create session factory for producing database sessions.
    
    Args:
        engine: Async SQLAlchemy engine
    
    Returns:
        Session factory configured for async sessions
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False  # Keep objects usable after commit
    )


# Initialize engine and session factory at module level
settings = get_settings()
engine = create_engine(settings.database_url)
session_factory = create_session_factory(engine)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for obtaining database sessions.
    
    Provides a database session with proper lifecycle management:
    - Yields a valid session for the request
    - Commits on success
    - Rolls back on exception
    - Always closes the session
    
    Yields:
        AsyncSession: Database session for the request
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
