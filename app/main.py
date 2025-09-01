from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import setup_middleware
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application starting up", version=settings.app_version, environment=settings.environment)
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Backend Application with GenAI Features",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Setup all middleware
setup_middleware(app)

# Include API routers
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to AI-Powered Backend API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1
    )
