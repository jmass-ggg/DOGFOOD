"""Pytest configuration and fixtures for tests."""

import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables before any app imports
# This must happen at module level before pytest collects tests
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost:5432/testdb"

from app.main import app, get_db_session
from app.models import Base


# ========================================================================
# Database Fixtures
# ========================================================================

@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Provide test database URL.
    
    Returns database URL for test database. Can be overridden via
    DATABASE_URL environment variable.
    
    Requirements: 10.1, 10.2 - Configure test database
    """
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/testdb"
    )


@pytest.fixture(scope="session")
async def test_engine(test_database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create async database engine for tests.
    
    Provides a session-scoped database engine that can be shared across
    all tests. The engine is disposed of after all tests complete.
    
    Requirements: 10.1, 10.2 - Provide test database engine
    """
    engine = create_async_engine(
        test_database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    
    yield engine
    
    # Cleanup: dispose engine after all tests
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide isolated database session for each test.
    
    Creates a new database session for each test function with proper
    transaction management. The session is rolled back after each test
    to maintain test isolation.
    
    Requirements: 10.1, 10.2, 10.3 - Provide isolated test database sessions
    """
    # Create session factory
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback after test completes
            await session.rollback()


@pytest.fixture(scope="function")
async def test_db_with_tables(test_engine: AsyncEngine) -> AsyncGenerator[AsyncEngine, None]:
    """
    Provide database engine with tables created.
    
    Creates all tables defined in SQLAlchemy models before the test,
    and drops them after the test completes. Useful for integration
    tests that need actual database tables.
    
    Requirements: 10.2 - Provide test database with schema
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ========================================================================
# FastAPI Client Fixtures
# ========================================================================

@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide async HTTP client for testing FastAPI endpoints.
    
    Creates an HTTPX AsyncClient configured to test the FastAPI
    application. Uses ASGI transport for direct app testing without
    network overhead.
    
    Requirements: 10.1, 10.3 - Provide test client for API testing
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def test_client_with_db(
    test_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide async HTTP client with database session override.
    
    Creates an HTTPX AsyncClient with a test database session injected
    via dependency override. Useful for integration tests that need
    database operations with proper test isolation.
    
    Requirements: 10.1, 10.3 - Provide test client with test database
    """
    # Override database dependency with test session
    async def override_get_db_session():
        yield test_db_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    # Cleanup: clear dependency overrides
    app.dependency_overrides.clear()


# ========================================================================
# Hypothesis Configuration
# ========================================================================

# Hypothesis settings are configured in pyproject.toml:
# - max_examples = 100 (minimum iterations per property test)
# - Additional profiles can be added as needed
#
# Property-based tests should use @given decorator from hypothesis
# and reference their design document property in docstrings.
#
# Requirements: 10.4, 10.5 - Configure property-based testing

