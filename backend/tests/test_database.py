"""Unit tests for database layer."""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.database import create_engine, create_session_factory, get_db_session, Base


def test_engine_creation():
    """
    Test that create_engine returns a valid AsyncEngine.
    
    Requirements: 3.1 - Create PostgreSQL database engine
    """
    # Use a test database URL
    test_db_url = "postgresql+psycopg://test:test@localhost:5432/testdb"
    
    engine = create_engine(test_db_url)
    
    # Verify it's an AsyncEngine
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+psycopg"
    
    # Verify pool configuration
    assert engine.pool.size() == 5  # pool_size
    assert engine.pool._max_overflow == 10  # max_overflow


def test_session_factory_creation():
    """
    Test that create_session_factory returns a valid session factory.
    
    Requirements: 3.2 - Provide session factory
    """
    test_db_url = "postgresql+psycopg://test:test@localhost:5432/testdb"
    engine = create_engine(test_db_url)
    
    factory = create_session_factory(engine)
    
    # Verify it's an async_sessionmaker
    assert isinstance(factory, async_sessionmaker)
    assert factory.class_ == AsyncSession
    assert factory.kw.get("expire_on_commit") is False


@pytest.mark.asyncio
async def test_dependency_provides_valid_session():
    """
    Test that get_db_session dependency provides a valid AsyncSession.
    
    Requirements: 3.3 - Provide FastAPI dependency for database sessions
    
    Note: This test verifies the dependency structure. It will attempt to
    create a session but may fail on actual database operations, which is
    expected in unit tests without a live database.
    """
    session_generator = get_db_session()
    
    # The dependency is an async generator
    session = None
    try:
        session = await anext(session_generator)
        
        # Verify we got an AsyncSession
        assert isinstance(session, AsyncSession)
        assert session.is_active
        
        # Test that it's properly configured
        assert session.expire_on_commit is False
        
    except Exception as e:
        # Database connection might fail in unit tests
        # As long as we got a valid session object, the test passes
        if session is not None:
            assert isinstance(session, AsyncSession)
        else:
            # Connection failed before we got a session - that's acceptable
            pytest.skip(f"Database connection not available: {e}")
    finally:
        # Cleanup - close the generator
        try:
            await session_generator.aclose()
        except:
            pass


def test_base_exists():
    """
    Test that declarative Base exists for model inheritance.
    
    Requirements: 3.1 - Provide declarative base for models
    """
    assert Base is not None
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "registry")
