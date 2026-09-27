"""Property-based tests for request ID middleware."""

import uuid
from hypothesis import given, strategies as st, settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.request_id import RequestIDMiddleware


@given(
    request_id=st.text(
        min_size=1,
        max_size=100,
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
    )
)
def test_property_request_id_propagation(request_id: str):
    """
    Feature: backend-foundation, Property 6: Request ID Propagation
    
    For any HTTP request that includes an X-Request-ID header, the response
    should include the same request ID in its X-Request-ID header.
    
    Validates: Requirements 6.1
    """
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_route():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Send request with the generated X-Request-ID header
    response = client.get("/test", headers={"X-Request-ID": request_id})
    
    # Verify the response includes the same request ID
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == request_id


@given(
    endpoint=st.sampled_from(["/test", "/health", "/api/test", "/api/v1/test"]),
    method=st.sampled_from(["GET", "POST", "PUT", "DELETE"])
)
@settings(max_examples=100)
def test_property_request_id_generation(endpoint: str, method: str):
    """
    Feature: backend-foundation, Property 7: Request ID Generation
    
    For any HTTP request without an X-Request-ID header, the response should
    include a valid UUID in the X-Request-ID header.
    
    Validates: Requirements 6.2
    """
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    # Register routes for all methods
    @app.get(endpoint)
    @app.post(endpoint)
    @app.put(endpoint)
    @app.delete(endpoint)
    async def test_route():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Send request WITHOUT X-Request-ID header
    response = client.request(method, endpoint)
    
    # Verify the response includes a request ID
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Verify the request ID is a valid UUID
    request_id = response.headers["X-Request-ID"]
    try:
        uuid_obj = uuid.UUID(request_id)
        # Verify it's a valid UUID string representation
        assert str(uuid_obj) == request_id
    except (ValueError, AttributeError) as e:
        raise AssertionError(f"Generated request ID '{request_id}' is not a valid UUID: {e}")
