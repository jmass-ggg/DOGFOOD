"""FastAPI application factory and health endpoint."""

from contextlib import asynccontextmanager
import logging

from fastapi import APIRouter, Depends, FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import engine, get_db_session

# Health check router
router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """
    Health check endpoint.
    
    Verifies service is running and database is accessible.
    
    Returns:
        dict: Health status including service name and database connectivity
    """
    # Test database connectivity with SELECT 1
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logging.getLogger("dogfood.health").warning("Database health check failed: %s", type(exc).__name__)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={
            "status": "unhealthy",
            "service": "dogfood-api",
            "database": "disconnected",
        })

    return {
        "status": "ok",
        "service": "dogfood-api",
        "database": "connected"
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    # Configure logging first so it's available during startup
    from app.core.logging import configure_logging
    configure_logging(settings.log_level)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Install middleware
    from app.core.request_id import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)
    
    # Register exception handlers
    from app.core.errors import (
        ApplicationError,
        application_error_handler,
        generic_exception_handler,
        http_exception_handler,
        validation_exception_handler,
    )
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Include routers
    app.include_router(router)
    
    return app


# Application instance
app = create_app()
