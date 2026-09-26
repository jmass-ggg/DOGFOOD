"""Property-based tests for error handling infrastructure."""

from hypothesis import given, strategies as st, settings
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.errors import ApplicationError, application_error_handler
from app.core.request_id import RequestIDMiddleware


# Strategy for generating valid error codes (uppercase alphanumeric with underscores)
error_codes = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_")
).filter(lambda x: len(x) > 0 and not x.startswith("_") and not x.endswith("_"))

# Strategy for error messages
error_messages = st.text(min_size=1, max_size=500)

# Strategy for error details (dictionaries with string keys and various values)
error_details = st.dictionaries(
    keys=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    values=st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none()
    ),
    max_size=10
)

# Strategy for HTTP status codes (common error status codes)
error_status_codes = st.sampled_from([
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
    status.HTTP_409_CONFLICT,
    status.HTTP_422_UNPROCESSABLE_ENTITY,
    status.HTTP_500_INTERNAL_SERVER_ERROR,
])


@given(
    error_code=error_codes,
    error_message=error_messages,
    error_details=error_details,
    error_status_code=error_status_codes
)
@settings(max_examples=100)
def test_property_error_response_structure(
    error_code: str,
    error_message: str,
    error_details: dict,
    error_status_code: int
):
    """
    Feature: backend-foundation, Property 10: Error Response Structure
    
    For any ApplicationError raised during request processing, the response should be
    a JSON object containing an "error" object with "code", "message", and "details"
    fields, and a "request_id" field.
    
    Validates: Requirements 7.1, 7.2, 7.3
    """
    # Create a minimal FastAPI app with error handling
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(ApplicationError, application_error_handler)
    
    # Create a route that raises ApplicationError with the generated values
    @app.get("/test-error")
    async def test_route():
        raise ApplicationError(
            code=error_code,
            message=error_message,
            details=error_details,
            status_code=error_status_code
        )
    
    client = TestClient(app, raise_server_exceptions=False)
    
    # Make request to trigger the error
    response = client.get("/test-error")
    
    # Verify status code matches
    assert response.status_code == error_status_code
    
    # Verify response is JSON
    assert response.headers.get("content-type") == "application/json"
    
    # Parse response body
    data = response.json()
    
    # Verify top-level structure: must have "error" and "request_id"
    assert "error" in data, "Response must contain 'error' field"
    assert "request_id" in data, "Response must contain 'request_id' field"
    
    # Verify error object structure
    error = data["error"]
    assert isinstance(error, dict), "Error field must be a dictionary"
    
    # Verify required error fields
    assert "code" in error, "Error object must contain 'code' field"
    assert "message" in error, "Error object must contain 'message' field"
    assert "details" in error, "Error object must contain 'details' field"
    
    # Verify field values match the ApplicationError
    assert error["code"] == error_code, f"Error code should be '{error_code}'"
    assert error["message"] == error_message, f"Error message should be '{error_message}'"
    assert error["details"] == error_details, f"Error details should match"
    
    # Verify request_id is present and non-empty
    assert isinstance(data["request_id"], str), "Request ID must be a string"
    assert len(data["request_id"]) > 0, "Request ID must not be empty"
