# Implementation Plan: Backend Foundation

## Overview

This implementation plan breaks down the backend foundation into discrete coding steps, building infrastructure incrementally and validating functionality as we go. The approach prioritizes getting core infrastructure working early, then layering in additional capabilities.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create backend/ directory structure with app/, tests/, migrations/ directories
  - Create pyproject.toml with FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic, pytest, HTTPX, Hypothesis dependencies
  - Create .env.example with placeholder configuration values
  - Create basic README.md with setup instructions
  - _Requirements: 1.4, 11.2_

- [x] 2. Implement configuration management
  - [x] 2.1 Create app/config.py with Pydantic Settings
    - Implement Settings class with all required configuration fields
    - Add type hints and default values
    - Configure env_file loading
    - _Requirements: 1.1, 1.2, 1.3_
   
  - [x] 2.2 Write unit tests for configuration
    - Test required settings are present
    - Test default values are applied
    - Test .env.example contains no secrets
    - _Requirements: 1.2, 1.3, 1.4_
  
  - [x] 2.3 Write property test for configuration loading
    - **Property 1: Configuration Loading**
    - **Validates: Requirements 1.1**

- [x] 3. Implement clock abstraction
  - [x] 3.1 Create app/core/clock.py with UTCClock
    - Implement Clock protocol
    - Implement UTCClock.now() returning timezone-aware UTC datetime
    - _Requirements: 9.1, 9.2_
  
  - [x] 3.2 Write unit tests for clock
    - Test clock.now() returns datetime
    - Test timezone awareness
    - _Requirements: 9.1, 9.2_
  
  - [ ]* 3.3 Write property test for clock timezone
    - **Property 15: Clock Timezone Awareness**
    - **Validates: Requirements 9.2**

- [-] 4. Implement database layer
  - [x] 4.1 Create app/core/database.py with SQLAlchemy setup
    - Implement create_engine with async PostgreSQL connection
    - Implement create_session_factory with AsyncSession
    - Implement get_db_session dependency with proper lifecycle management
    - Create declarative Base
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.2 Write unit tests for database setup
    - Test engine creation
    - Test session factory creation
    - Test dependency provides valid session
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 4.3 Write property test for session validity
    - **Property 2: Database Session Validity**
    - **Validates: Requirements 3.4**
  
  - [ ]* 4.4 Write property test for session cleanup
    - **Property 3: Database Session Cleanup**
    - **Validates: Requirements 3.5**

- [-] 5. Initialize Alembic migrations
  - [x] 5.1 Set up Alembic configuration
    - Run alembic init migrations
    - Configure alembic.ini with database connection
    - Update env.py to use SQLAlchemy metadata
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 5.2 Write unit tests for Alembic setup
    - Test alembic.ini exists and is valid
    - Test migrations directory structure
    - _Requirements: 4.1_

- [x] 6. Checkpoint - Verify database connectivity
  - Ensure database engine and Alembic are configured correctly, ask the user if questions arise.

- [-] 7. Implement request ID middleware
  - [x] 7.1 Create app/core/request_id.py
    - Implement RequestIDMiddleware using BaseHTTPMiddleware
    - Implement request_id_context ContextVar
    - Implement get_request_id() function
    - Handle X-Request-ID header extraction and UUID generation
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 7.2 Write unit tests for request ID middleware
    - Test propagation of provided request ID
    - Test generation of UUID when missing
    - Test response header inclusion
    - _Requirements: 6.1, 6.2, 6.4_
  
  - [x] 7.3 Write property test for request ID propagation
    - **Property 6: Request ID Propagation**
    - **Validates: Requirements 6.1**
  
  - [x] 7.4 Write property test for request ID generation
    - **Property 7: Request ID Generation**
    - **Validates: Requirements 6.2**
  
  - [ ]* 7.5 Write property test for request ID availability
    - **Property 8: Request ID Availability**
    - **Validates: Requirements 6.3**
  
  - [ ]* 7.6 Write property test for request ID in response
    - **Property 9: Request ID in Response**
    - **Validates: Requirements 6.4**

- [-] 8. Implement logging infrastructure
  - [x] 8.1 Create app/core/logging.py
    - Implement configure_logging function
    - Implement RequestIDFilter for adding request_id to log records
    - Configure structured log format with request context
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 8.2 Write unit tests for logging
    - Test logger configuration
    - Test request ID filter
    - Test log level configuration
    - _Requirements: 8.1, 8.3, 8.4_
  
  - [x] 8.3 Write property test for request logging
    - **Property 12: Request Logging**
    - **Validates: Requirements 8.1, 8.4**
  
  - [x] 8.4 Write property test for log security
    - **Property 13: Log Security**
    - **Validates: Requirements 8.2**
  
  - [ ]* 8.5 Write property test for log level configuration
    - **Property 14: Log Level Configuration**
    - **Validates: Requirements 8.3**

- [-] 9. Implement error handling
  - [x] 9.1 Create app/core/errors.py
    - Implement ApplicationError exception class
    - Implement application_error_handler for ApplicationError
    - Implement generic_exception_handler for unhandled exceptions
    - Include request_id in all error responses
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 9.2 Write unit tests for error handling
    - Test ApplicationError formatting
    - Test unhandled exception handling
    - Test request ID inclusion
    - Test status codes
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 9.3 Write property test for error response structure
    - **Property 10: Error Response Structure**
    - **Validates: Requirements 7.1, 7.2, 7.3**
  
  - [ ]* 9.4 Write property test for unhandled exception handling
    - **Property 11: Unhandled Exception Handling**
    - **Validates: Requirements 7.4**

- [-] 10. Implement health endpoint
  - [x] 10.1 Create health check endpoint in app/main.py
    - Implement GET /health route
    - Perform SELECT 1 database connectivity check
    - Return status, service name, and database status
    - Handle database connection failures gracefully
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 10.2 Write unit tests for health endpoint
    - Test successful health check with connected database
    - Test unhealthy response with disconnected database
    - Test response structure
    - Test no sensitive data exposure
    - _Requirements: 5.1, 5.3, 5.4, 5.5_
  
  - [x] 10.3 Write property test for health endpoint response
    - **Property 4: Health Endpoint Response**
    - **Validates: Requirements 5.1, 5.3, 5.4**
  
  - [ ]* 10.4 Write property test for health response security
    - **Property 5: Health Response Security**
    - **Validates: Requirements 5.5**

- [-] 11. Create FastAPI application factory
  - [x] 11.1 Implement create_app() in app/main.py
    - Create FastAPI instance with appropriate configuration
    - Install RequestIDMiddleware
    - Register exception handlers (ApplicationError, generic Exception)
    - Include health router
    - Call configure_logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 11.2 Write unit tests for application initialization
    - Test FastAPI app creation
    - Test middleware installation
    - Test exception handler registration
    - Test router inclusion
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 12. Checkpoint - Run all tests and verify functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Create Docker infrastructure
  - [x] 13.1 Create Dockerfile
    - Use Python 3.12+ base image
    - Install dependencies from pyproject.toml
    - Set up working directory
    - Expose appropriate port
    - Configure uvicorn as entrypoint
    - _Requirements: 11.1_
  
  - [x] 13.2 Write unit test for Docker setup
    - Test Dockerfile exists and is valid
    - _Requirements: 11.1_

- [x] 14. Update README with comprehensive setup instructions
  - [x] 14.1 Document setup and usage
    - Add dependency installation instructions
    - Add .env configuration instructions
    - Add PostgreSQL setup instructions
    - Add Alembic migration instructions
    - Add FastAPI startup instructions
    - Add test execution instructions
    - _Requirements: 11.2_
  
  - [ ]* 14.2 Write unit test for documentation completeness
    - Test README covers all required topics
    - _Requirements: 11.2_

- [ ] 15. Configure pytest and test infrastructure
  - [x] 15.1 Create tests/conftest.py with shared fixtures
    - Create test database fixture
    - Create test FastAPI client fixture
    - Configure pytest-asyncio
    - Set up Hypothesis profiles for property-based testing
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 15.2 Write unit test for pytest configuration
    - Test pytest is configured correctly
    - Test fixtures are available
    - _Requirements: 10.1_

- [x] 16. Final checkpoint - Complete verification
  - Run all tests including property-based tests with 100+ iterations
  - Verify FastAPI starts successfully
  - Verify /health endpoint responds correctly
  - Verify no secrets in .env.example
  - Verify Docker build succeeds
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties across many inputs
- Unit tests validate specific examples, integration points, and edge cases
- All property-based tests should run minimum 100 iterations
