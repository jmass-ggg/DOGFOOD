"""Property-based tests for authentication functionality."""

import pytest
import uuid
import time
from hypothesis import given, strategies as st, settings, assume, HealthCheck


# ========================================================================
# Property 6: Invalid Credentials Generic Error
# ========================================================================

@given(
    test_id=st.uuids(),
    valid_password=st.text(min_size=8, max_size=100),
    wrong_password=st.text(min_size=8, max_size=100)
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline to prevent flakiness from timing issues
)
@pytest.mark.asyncio
async def test_property_invalid_credentials_generic_error(
    test_client_with_db,
    test_id: uuid.UUID,
    valid_password: str,
    wrong_password: str
):
    """
    Feature: authentication-and-public-api, Property 6: Invalid Credentials Generic Error
    
    For any login attempt with either non-existent email or incorrect password,
    the error message should be generic and not reveal which credential was invalid.
    
    Validates: Requirements 3.2, 3.3, 3.6
    """
    # Ensure passwords are different to test wrong password case
    assume(valid_password != wrong_password)
    
    # Generate unique email and username using UUID and timestamp to avoid collisions
    timestamp_ns = time.time_ns()
    test_id_str = str(test_id).replace("-", "")[:10]
    unique_suffix = f"{test_id_str}{timestamp_ns}"
    valid_email = f"user{unique_suffix}@test.com"
    wrong_email = f"wrong{unique_suffix}@test.com"
    username = f"user{unique_suffix}"
    
    # Step 1: Register a user with valid credentials
    registration_data = {
        "email": valid_email,
        "username": username,
        "password": valid_password,
        "full_name": "Test User",
    }
    
    register_response = await test_client_with_db.post(
        "/api/v1/auth/register",
        json=registration_data
    )
    
    # If registration fails due to duplicate, skip this iteration
    if register_response.status_code == 409:
        assume(False)
    
    # For other failures, we want to know about them
    assert register_response.status_code == 201, (
        f"Registration failed unexpectedly: {register_response.status_code} - "
        f"{register_response.text}"
    )

    # Step 2: Try to login with non-existent email
    login_with_wrong_email = {
        "email": wrong_email,
        "password": valid_password
    }
    
    response_wrong_email = await test_client_with_db.post(
        "/api/v1/auth/login",
        json=login_with_wrong_email
    )
    
    # Step 3: Try to login with wrong password (but correct email)
    login_with_wrong_password = {
        "email": valid_email,
        "password": wrong_password
    }
    
    response_wrong_password = await test_client_with_db.post(
        "/api/v1/auth/login",
        json=login_with_wrong_password
    )
    
    # Both should return 401 Unauthorized
    assert response_wrong_email.status_code == 401, (
        f"Expected 401 for non-existent email, got {response_wrong_email.status_code}"
    )
    assert response_wrong_password.status_code == 401, (
        f"Expected 401 for wrong password, got {response_wrong_password.status_code}"
    )
    
    # Extract error messages
    data_wrong_email = response_wrong_email.json()
    data_wrong_password = response_wrong_password.json()
    
    error_msg_wrong_email = (
        data_wrong_email.get("detail") or 
        (data_wrong_email.get("error", {}).get("message", ""))
    )
    error_msg_wrong_password = (
        data_wrong_password.get("detail") or 
        (data_wrong_password.get("error", {}).get("message", ""))
    )
    
    # Property: Error messages should be identical (generic)
    # This prevents attackers from enumerating valid emails
    assert error_msg_wrong_email.lower() == error_msg_wrong_password.lower(), (
        f"Error messages differ: non-existent email returned '{error_msg_wrong_email}' "
        f"but wrong password returned '{error_msg_wrong_password}'. "
        f"This reveals which credential was invalid."
    )
    
    # Property: Error message should be generic and not reveal specific credential
    error_msg_lower = error_msg_wrong_email.lower()
    
    # Should mention authentication/credentials failed
    assert (
        "incorrect" in error_msg_lower or 
        "invalid" in error_msg_lower or
        "unauthorized" in error_msg_lower
    ), f"Error message '{error_msg_wrong_email}' does not indicate authentication failure"
    
    # Should not specifically mention which credential was wrong
    # If message contains "email", it should also contain "password" (i.e., both)
    # If it mentions only one, it's revealing information
    has_email_keyword = "email" in error_msg_lower
    has_password_keyword = "password" in error_msg_lower
    
    # If one is mentioned, both must be mentioned (or neither)
    assert has_email_keyword == has_password_keyword, (
        f"Error message '{error_msg_wrong_email}' mentions one credential specifically, "
        f"which could reveal which credential was invalid"
    )
