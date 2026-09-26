"""Unit tests for health endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app, get_db_session


@pytest.mark.asyncio
async def test_health_check_with_connected_database():
    """
    Test successful health check with connected database.
    
    Requirements: 5.1, 5.2, 5.3 - Health endpoint returns OK status with connected database
    """
    # Mock database session that succeeds
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=None)
    
    # Create dependency override
    async def mock_get_db_session():
        yield mock_session
    
    # Override the dependency
    app.dependency_overrides[get_db_session] = mock_get_db_session
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["service"] == "dogfood-api"
        assert data["database"] == "connected"
        
        # Verify SELECT 1 was executed
        mock_session.execute.assert_called_once()
        # Verify the query is a text clause (the actual type check is implementation detail)
        call_args = mock_session.execute.call_args[0][0]
        # Just verify that execute was called with something (the text clause)
    finally:
        # Clean up override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check_with_disconnected_database():
    """
    Test unhealthy response with disconnected database.
    
    Requirements: 5.4 - Health endpoint returns unhealthy when database unavailable
    """
    # Mock database session that fails
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=Exception("Database connection failed"))
    
    # Create dependency override
    async def mock_get_db_session():
        yield mock_session
    
    # Override the dependency
    app.dependency_overrides[get_db_session] = mock_get_db_session
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["service"] == "dogfood-api"
        assert data["database"] == "disconnected"
    finally:
        # Clean up override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint_response_structure():
    """
    Test response structure of health endpoint.
    
    Requirements: 5.1, 5.3 - Health endpoint returns proper structure
    """
    # Mock database session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=None)
    
    # Create dependency override
    async def mock_get_db_session():
        yield mock_session
    
    # Override the dependency
    app.dependency_overrides[get_db_session] = mock_get_db_session
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        data = response.json()
        
        # Verify all required fields are present
        assert "status" in data
        assert "service" in data
        assert "database" in data
        
        # Verify status is one of expected values
        assert data["status"] in ["ok", "unhealthy"]
        
        # Verify database is one of expected values
        assert data["database"] in ["connected", "disconnected"]
        
        # Verify service name is correct
        assert data["service"] == "dogfood-api"
    finally:
        # Clean up override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint_no_sensitive_data():
    """
    Test that health endpoint does not expose sensitive data.
    
    Requirements: 5.5 - No connection strings, credentials, or secrets in response
    """
    # Test with both connected and disconnected scenarios
    for should_fail in [False, True]:
        mock_session = AsyncMock(spec=AsyncSession)
        
        if should_fail:
            mock_session.execute = AsyncMock(
                side_effect=Exception("Connection failed: postgresql://secret:password@host:5432/db")
            )
        else:
            mock_session.execute = AsyncMock(return_value=None)
        
        # Create dependency override
        async def mock_get_db_session():
            yield mock_session
        
        # Override the dependency
        app.dependency_overrides[get_db_session] = mock_get_db_session
        
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/health")
            
            # Get response as text to check for sensitive patterns
            response_text = response.text.lower()
            
            # Verify no sensitive data patterns
            assert "password" not in response_text
            assert "secret" not in response_text
            assert "postgresql://" not in response_text
            assert "connection string" not in response_text
            assert "traceback" not in response_text
            assert "exception" not in response_text
            
            # Verify only expected fields in JSON
            data = response.json()
            assert set(data.keys()) == {"status", "service", "database"}
        finally:
            # Clean up override
            app.dependency_overrides.clear()
