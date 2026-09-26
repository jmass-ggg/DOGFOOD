"""Property-based tests for database layer."""

import pytest
from hypothesis import given, strategies as st
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session


@given(
    query_value=st.integers(min_value=1, max_value=1000)
)
@pytest.mark.asyncio
async def test_property_database_session_validity(query_value: int):
    """
    Feature: backend-foundation, Property 2: Database Session Validity
    
    For any database session request through the dependency, the returned session
    should be a valid SQLAlchemy AsyncSession that can execute queries.
    
    Validates: Requirements 3.4
    """
    # Get a session from the dependency
    session_generator = get_db_session()
    
    try:
        # Get the session from the async generator
        session = await anext(session_generator)
        
        # Verify it's a valid AsyncSession
        assert isinstance(session, AsyncSession)
        assert session.is_active
        
        # Verify the session can execute queries
        # Use the generated query_value to test different values
        result = await session.execute(text(f"SELECT {query_value}"))
        row = result.scalar()
        
        # Verify the query executed correctly
        assert row == query_value
        
    finally:
        # Cleanup - close the generator
        await session_generator.aclose()
