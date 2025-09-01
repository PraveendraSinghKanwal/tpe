import time
from fastapi import APIRouter

from app.core.monitoring import metrics_endpoint
from app.config import settings

router = APIRouter()

# Health check endpoint
@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": time.time()
    }


# Metrics endpoint
@router.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return await metrics_endpoint()
