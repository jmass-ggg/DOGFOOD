"""FastAPI application factory and health endpoint."""

from fastapi import APIRouter, Depends, FastAPI, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db_session

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
    database_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        # Gracefully handle database connection failures
        pass
    
    # Determine overall status based on database connectivity
    overall_status = "ok" if database_status == "connected" else "unhealthy"
    
    return {
        "status": overall_status,
        "service": "dogfood-api",
        "database": database_status
    }


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
        version="1.0.0"
    )
    
    # Install middleware
    from app.core.request_id import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)
    
    # Register exception handlers
    from app.core.errors import (
        ApplicationError,
        application_error_handler,
        generic_exception_handler,
    )
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # Include routers
    app.include_router(router)
    
    return app


# Application instance
app = create_app()
