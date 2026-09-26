"""Property-based tests for health endpoint."""

import pytest
from hypothesis import given, strategies as st
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app, get_db_session


@given(
    database_connected=st.booleans()
)
@pytest.mark.asyncio
async def test_property_health_endpoint_response(database_connected: bool):
    """
    Feature: backend-foundation, Property 4: Health Endpoint Response
    
    For any GET request to /health, the response should contain "status", "service",
    and "database" fields, where "database" is either "connected" or "disconnected",
    and "status" matches the database state ("ok" if connected, "unhealthy" otherwise).
    
    Validates: Requirements 5.1, 5.3, 5.4
    """
    # Mock database session based on the generated database_connected value
    mock_session = AsyncMock(spec=AsyncSession)
    
    if database_connected:
        # Database is connected - execute succeeds
        mock_session.execute = AsyncMock(return_value=None)
    else:
        # Database is disconnected - execute fails
        mock_session.execute = AsyncMock(side_effect=Exception("Database connection failed"))
    
    # Create dependency override
    async def mock_get_db_session():
        yield mock_session
    
    # Override the dependency
    app.dependency_overrides[get_db_session] = mock_get_db_session
    
    try:
        # Make request to health endpoint
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        
        assert response.status_code == (200 if database_connected else 503)
        
        # Parse response JSON
        data = response.json()
        
        # Property: Response must contain exactly the required fields
        assert "status" in data, "Response must contain 'status' field"
        assert "service" in data, "Response must contain 'service' field"
        assert "database" in data, "Response must contain 'database' field"
        
        # Property: database field must be either "connected" or "disconnected"
        assert data["database"] in ["connected", "disconnected"], \
            f"database field must be 'connected' or 'disconnected', got '{data['database']}'"
        
        # Property: database field must match the actual connectivity state
        expected_database = "connected" if database_connected else "disconnected"
        assert data["database"] == expected_database, \
            f"database field should be '{expected_database}' when database_connected={database_connected}"
        
        # Property: status must be "ok" if connected, "unhealthy" otherwise
        expected_status = "ok" if database_connected else "unhealthy"
        assert data["status"] == expected_status, \
            f"status should be '{expected_status}' when database is '{expected_database}'"
        
        # Property: service name is consistent
        assert data["service"] == "dogfood-api", \
            "service field must always be 'dogfood-api'"
        
    finally:
        # Clean up override
        app.dependency_overrides.clear()
