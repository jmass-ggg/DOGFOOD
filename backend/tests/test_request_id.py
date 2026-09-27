"""Unit tests for request ID middleware."""

import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.request_id import RequestIDMiddleware, get_request_id, request_id_context


def test_propagation_of_provided_request_id():
    """Test that a provided X-Request-ID header is propagated to the response.
    
    Validates: Requirements 6.1
    """
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_route():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Send request with X-Request-ID header
    provided_id = "test-request-id-123"
    response = client.get("/test", headers={"X-Request-ID": provided_id})
    
    # Verify the same request ID is in the response header
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == provided_id


def test_generation_of_uuid_when_missing():
    """Test that a UUID is generated when X-Request-ID header is not provided.
    
    Validates: Requirements 6.2
    """
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_route():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Send request without X-Request-ID header
    response = client.get("/test")
    
    # Verify a request ID was generated and is in the response
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Verify it's a valid UUID
    request_id = response.headers["X-Request-ID"]
    try:
        uuid.UUID(request_id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    
    assert is_valid_uuid, f"Generated request ID '{request_id}' is not a valid UUID"


def test_response_header_inclusion():
    """Test that X-Request-ID header is always included in responses.
    
    Validates: Requirements 6.4
    """
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test")
    async def test_route():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Test with provided request ID
    response1 = client.get("/test", headers={"X-Request-ID": "custom-id"})
    assert "X-Request-ID" in response1.headers
    
    # Test without provided request ID
    response2 = client.get("/test")
    assert "X-Request-ID" in response2.headers


def test_request_id_availability_during_processing():
    """Test that request ID is accessible via get_request_id() during request processing.
    
    Validates: Requirements 6.3
    """
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    captured_request_id = None
    
    @app.get("/test")
    async def test_route():
        nonlocal captured_request_id
        captured_request_id = get_request_id()
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Test with provided request ID
    provided_id = "test-id-456"
    response = client.get("/test", headers={"X-Request-ID": provided_id})
    
    assert response.status_code == 200
    assert captured_request_id == provided_id
    assert captured_request_id == response.headers["X-Request-ID"]


def test_context_isolation_between_requests():
    """Test that request IDs are properly isolated between different requests."""
    # Create a minimal FastAPI app with the middleware
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    captured_ids = []
    
    @app.get("/test")
    async def test_route():
        captured_ids.append(get_request_id())
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Make multiple requests with different IDs
    id1 = "request-1"
    id2 = "request-2"
    id3 = "request-3"
    
    response1 = client.get("/test", headers={"X-Request-ID": id1})
    response2 = client.get("/test", headers={"X-Request-ID": id2})
    response3 = client.get("/test", headers={"X-Request-ID": id3})
    
    # Verify each request had the correct ID during processing
    assert len(captured_ids) == 3
    assert captured_ids[0] == id1
    assert captured_ids[1] == id2
    assert captured_ids[2] == id3
    
    # Verify response headers match
    assert response1.headers["X-Request-ID"] == id1
    assert response2.headers["X-Request-ID"] == id2
    assert response3.headers["X-Request-ID"] == id3


def test_unsafe_request_id_is_replaced():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_route():
        return {"request_id": get_request_id()}

    client = TestClient(app)
    for supplied in (" ", "Bearer secret", "abc.def.ghi"):
        response = client.get("/test", headers={"X-Request-ID": supplied})
        generated = response.headers["X-Request-ID"]
        assert uuid.UUID(generated)
        assert generated == response.json()["request_id"]
