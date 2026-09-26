"""Test that conftest.py fixtures work correctly."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


@pytest.mark.asyncio
async def test_test_engine_fixture(test_engine: AsyncEngine):
    """
    Verify test_engine fixture provides valid AsyncEngine.
    
    Requirements: 10.1, 10.2 - Test database engine fixture
    """
    assert test_engine is not None
    assert isinstance(test_engine, AsyncEngine)
    assert test_engine.url.drivername == "postgresql+psycopg"


@pytest.mark.asyncio
async def test_test_db_session_fixture(test_db_session: AsyncSession):
    """
    Verify test_db_session fixture provides valid AsyncSession.
    
    Requirements: 10.1, 10.2, 10.3 - Test database session fixture
    """
    assert test_db_session is not None
    assert isinstance(test_db_session, AsyncSession)
    assert test_db_session.is_active


@pytest.mark.asyncio
async def test_test_client_fixture(test_client: AsyncClient):
    """
    Verify test_client fixture provides valid AsyncClient.
    
    Requirements: 10.1, 10.3 - Test client fixture
    """
    assert test_client is not None
    assert isinstance(test_client, AsyncClient)
    
    # Test that client can make requests
    response = await test_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_test_client_with_db_fixture(test_client_with_db: AsyncClient):
    """
    Verify test_client_with_db fixture provides valid AsyncClient with DB override.
    
    Requirements: 10.1, 10.3 - Test client with database fixture
    """
    assert test_client_with_db is not None
    assert isinstance(test_client_with_db, AsyncClient)
    
    # Test that client can make requests
    response = await test_client_with_db.get("/health")
    assert response.status_code == 200


def test_test_database_url_fixture(test_database_url: str):
    """
    Verify test_database_url fixture provides valid URL.
    
    Requirements: 10.1, 10.2 - Test database URL fixture
    """
    assert test_database_url is not None
    assert isinstance(test_database_url, str)
    assert "postgresql" in test_database_url
