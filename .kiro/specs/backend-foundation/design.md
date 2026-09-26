# Design Document: Backend Foundation

## Overview

The Backend Foundation provides the core infrastructure layer for the DogFood hackathon platform. It establishes patterns for configuration management, database access, error handling, logging, and request tracking that all future domain modules will use. The design prioritizes simplicity, type safety, and modern Python/FastAPI patterns while avoiding premature abstraction.

## Architecture

### Technology Stack

- **Python 3.12+**: Modern Python with enhanced type hints
- **FastAPI**: Modern async web framework with automatic OpenAPI documentation
- **Pydantic v2**: Data validation and settings management using pydantic-settings
- **SQLAlchemy 2.x**: Modern ORM with type-safe patterns
- **PostgreSQL**: Primary database using psycopg (v3) driver
- **Alembic**: Database migration management
- **Pytest**: Testing framework with HTTPX for API testing
- **Uvicorn**: ASGI server for FastAPI

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application factory
│   ├── config.py                # Pydantic settings
│   │
│   └── core/
│       ├── __init__.py
│       ├── database.py          # SQLAlchemy engine, session factory, dependency
│       ├── errors.py            # Exception handlers and error responses
│       ├── logging.py           # Logging configuration
│       ├── request_id.py        # Request ID middleware
│       └── clock.py             # UTC clock abstraction
│
├── migrations/                   # Alembic migration directory
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   └── test_health.py           # Health endpoint tests
│
├── alembic.ini                  # Alembic configuration
├── pyproject.toml               # Dependencies and project metadata
├── Dockerfile                   # Container build definition
├── .env.example                 # Example environment variables
└── README.md                    # Setup and usage documentation
```

## Components and Interfaces

### Configuration Management (`app/config.py`)

Uses Pydantic Settings for type-safe configuration from environment variables.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_env: str = "development"
    app_name: str = "dogfood-api"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

settings = Settings()
```

### Database Layer (`app/core/database.py`)

Implements SQLAlchemy 2.x async patterns with proper session lifecycle management.

```python
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

Base = declarative_base()

# Engine creation
def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

# Session factory
def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

# FastAPI dependency
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Request ID Middleware (`app/core/request_id.py`)

Implements ASGI middleware for request tracking.

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextvars import ContextVar

request_id_context: ContextVar[str] = ContextVar("request_id", default="")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in context
        request_id_context.set(request_id)
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        return response

def get_request_id() -> str:
    return request_id_context.get()
```

### Error Handling (`app/core/errors.py`)

Provides structured error responses with consistent formatting.

```python
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

class ApplicationError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    from app.core.request_id import get_request_id
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "request_id": get_request_id()
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from app.core.request_id import get_request_id
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            },
            "request_id": get_request_id()
        }
    )
```

### Logging Infrastructure (`app/core/logging.py`)

Configures structured logging with request context.

```python
import logging
import sys
from typing import Any, Dict
from app.core.request_id import get_request_id

class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "N/A"
        return True

def configure_logging(log_level: str) -> None:
    # Configure root logger
    logging.basicConfig(
        level=log_level.upper(),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Add request ID filter
    for handler in logging.root.handlers:
        handler.addFilter(RequestIDFilter())
    
    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

### UTC Clock (`app/core/clock.py`)

Provides timezone-aware UTC timestamps.

```python
from datetime import datetime, timezone
from typing import Protocol

class Clock(Protocol):
    def now(self) -> datetime:
        """Return current UTC time with timezone awareness."""
        ...

class UTCClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

# Default clock instance
clock = UTCClock()
```

### Health Endpoint (`app/main.py`)

Implements health check with database connectivity verification.

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db_session

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db_session)):
    # Test database connectivity
    try:
        await db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        database_status = "disconnected"
    
    return {
        "status": "ok" if database_status == "connected" else "unhealthy",
        "service": "dogfood-api",
        "database": database_status
    }
```

### Application Factory (`app/main.py`)

Creates and configures the FastAPI application.

```python
from fastapi import FastAPI
from app.config import settings
from app.core.logging import configure_logging
from app.core.request_id import RequestIDMiddleware
from app.core.errors import application_error_handler, generic_exception_handler, ApplicationError

def create_app() -> FastAPI:
    # Configure logging
    configure_logging(settings.log_level)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0"
    )
    
    # Install middleware
    app.add_middleware(RequestIDMiddleware)
    
    # Install exception handlers
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Include routers
    app.include_router(router)
    
    return app

app = create_app()
```

## Data Models

No domain models are implemented in this phase. The database infrastructure provides:

- **Base**: SQLAlchemy declarative base for future model inheritance
- **AsyncEngine**: Database connection pool
- **AsyncSession**: Database session for transactions
- **Session Factory**: Factory for creating sessions

Future domain modules will define models inheriting from `Base` and use the session dependency for database operations.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Configuration Loading
*For any* valid environment variable with a corresponding configuration field, setting that environment variable should result in the configuration object containing that value.
**Validates: Requirements 1.1**

### Property 2: Database Session Validity
*For any* database session request through the dependency, the returned session should be a valid SQLAlchemy AsyncSession that can execute queries.
**Validates: Requirements 3.4**

### Property 3: Database Session Cleanup
*For any* database session lifecycle (successful or failed), the session should be properly closed and not leave open connections.
**Validates: Requirements 3.5**

### Property 4: Health Endpoint Response
*For any* GET request to /health, the response should contain "status", "service", and "database" fields, where "database" is either "connected" or "disconnected", and "status" matches the database state ("ok" if connected, "unhealthy" otherwise).
**Validates: Requirements 5.1, 5.3, 5.4**

### Property 5: Health Response Security
*For any* health endpoint response (healthy or unhealthy), the response body should not contain connection strings, credentials, host addresses, or stack traces.
**Validates: Requirements 5.5**

### Property 6: Request ID Propagation
*For any* HTTP request that includes an X-Request-ID header, the response should include the same request ID in its X-Request-ID header.
**Validates: Requirements 6.1**

### Property 7: Request ID Generation
*For any* HTTP request without an X-Request-ID header, the response should include a valid UUID in the X-Request-ID header.
**Validates: Requirements 6.2**

### Property 8: Request ID Availability
*For any* HTTP request, the request ID should be accessible via get_request_id() during request processing.
**Validates: Requirements 6.3**

### Property 9: Request ID in Response
*For any* HTTP response, the X-Request-ID header should be present.
**Validates: Requirements 6.4**

### Property 10: Error Response Structure
*For any* ApplicationError raised during request processing, the response should be a JSON object containing an "error" object with "code", "message", and "details" fields, and a "request_id" field.
**Validates: Requirements 7.1, 7.2, 7.3**

### Property 11: Unhandled Exception Handling
*For any* unhandled exception during request processing, the response should have status code 500 and contain a structured error response with code "INTERNAL_ERROR" and a request_id.
**Validates: Requirements 7.4**

### Property 12: Request Logging
*For any* HTTP request processed by the application, the logs should contain entries with request_id, HTTP method, path, response status, and duration.
**Validates: Requirements 8.1, 8.4**

### Property 13: Log Security
*For any* log entry, the message should not contain passwords, access tokens, refresh tokens, database credentials, or secret keys (tested via pattern matching).
**Validates: Requirements 8.2**

### Property 14: Log Level Configuration
*For any* valid log level setting (DEBUG, INFO, WARNING, ERROR, CRITICAL), configuring that log level should result in the logging system respecting that level.
**Validates: Requirements 8.3**

### Property 15: Clock Timezone Awareness
*For any* call to clock.now(), the returned datetime should be timezone-aware with UTC timezone.
**Validates: Requirements 9.2**



## Error Handling

### Error Response Format

All errors return JSON with consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  },
  "request_id": "uuid-v4"
}
```

### Error Categories

1. **Application Errors** (`ApplicationError`)
   - Business logic errors
   - Validation failures
   - Configurable status codes (400, 404, 409, etc.)
   - Structured with code, message, details

2. **Unhandled Exceptions**
   - Any uncaught exception
   - Returns 500 status
   - Code: "INTERNAL_ERROR"
   - Generic message (no stack trace exposure)

3. **Framework Errors** (FastAPI built-in)
   - Request validation (422)
   - Not found (404)
   - Method not allowed (405)
   - Handled by FastAPI's default handlers

### Security Considerations

- Never expose stack traces to clients
- Never include sensitive data in error responses
- Log full exception details server-side only
- Include request ID for error correlation

## Testing Strategy

### Dual Testing Approach

The Backend Foundation uses both **unit tests** and **property-based tests** as complementary testing strategies:

- **Unit tests**: Verify specific examples, integration points, and edge cases
- **Property-based tests**: Verify universal properties hold across many generated inputs

### Property-Based Testing

**Library**: [Hypothesis](https://hypothesis.readthedocs.io/) for Python

**Configuration**: Each property test runs a minimum of 100 iterations to ensure comprehensive coverage through randomization.

**Tagging**: Each property test references its design document property using a comment:

```python
@given(...)
def test_property_name(...):
    """
    Feature: backend-foundation, Property 1: Configuration Loading
    
    For any valid environment variable with a corresponding configuration field,
    setting that environment variable should result in the configuration object
    containing that value.
    """
    # Test implementation
```

**Property Test Coverage**:

1. **Property 1**: Configuration loading with various environment variable values
2. **Property 2**: Database session validity across different query patterns
3. **Property 3**: Database session cleanup under normal and error conditions
4. **Property 4**: Health endpoint response structure and correctness
5. **Property 5**: Health response security (no sensitive data leaks)
6. **Property 6**: Request ID propagation with various ID formats
7. **Property 7**: Request ID generation and UUID validity
8. **Property 8**: Request ID availability during request processing
9. **Property 9**: Request ID presence in all responses
10. **Property 10**: Error response structure for various error types
11. **Property 11**: Unhandled exception handling across exception types
12. **Property 12**: Request logging completeness
13. **Property 13**: Log security (no sensitive data in logs)
14. **Property 14**: Log level configuration effectiveness
15. **Property 15**: Clock timezone awareness

### Unit Testing

**Framework**: pytest with HTTPX for FastAPI testing

**Coverage Areas**:

1. **Configuration** (`test_config.py`)
   - Required settings presence (APP_ENV, DATABASE_URL, etc.)
   - Default value correctness
   - .env.example file validation (no secrets)

2. **Database** (`test_database.py`)
   - Engine creation
   - Session factory creation
   - Dependency function behavior
   - Connection pooling

3. **Health Endpoint** (`test_health.py`)
   - Successful health check with connected database
   - Unhealthy response with disconnected database
   - Response structure validation
   - No sensitive data exposure

4. **Request ID Middleware** (`test_request_id.py`)
   - Propagation of provided request ID
   - Generation of new UUID when missing
   - Context variable accessibility
   - Response header presence

5. **Error Handling** (`test_errors.py`)
   - ApplicationError formatting
   - Unhandled exception handling
   - Request ID inclusion in errors
   - Status code correctness

6. **Logging** (`test_logging.py`)
   - Logger configuration
   - Request ID filter application
   - Log level enforcement
   - Log format structure

7. **Clock** (`test_clock.py`)
   - UTC clock returns timezone-aware datetime
   - Datetime has UTC timezone

8. **Application Initialization** (`test_main.py`)
   - FastAPI app creation
   - Middleware installation
   - Exception handler registration
   - Router inclusion

9. **Alembic** (`test_migrations.py`)
   - Configuration file existence
   - Migration directory structure
   - SQLAlchemy metadata integration

10. **Docker** (`test_docker.py`)
    - Dockerfile existence and validity
    - README documentation completeness

### Testing Best Practices

- **Isolation**: Each test should be independent and not rely on execution order
- **Cleanup**: Database sessions and connections are properly closed in fixtures
- **Mocking**: Minimal mocking; prefer testing real integrations where practical
- **Fixtures**: Use pytest fixtures in `conftest.py` for shared test setup (test database, test client)
- **Async Support**: Use pytest-asyncio for async test functions
- **Coverage**: Aim for high coverage of core infrastructure, but prioritize meaningful tests over coverage metrics

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run property-based tests only
pytest -k "property"

# Run with verbose output
pytest -v
```

### Continuous Integration

Tests should run on:
- Pull request creation
- Commits to main branch
- Before deployment

All tests must pass before merging code changes.
