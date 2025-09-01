import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.logging import get_logger
from app.core.monitoring import MetricsMiddleware

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add unique request ID to each request."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class GlobalExceptionHandler:
    """Global exception handler for unhandled errors."""
    
    @staticmethod
    async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(
            "Unhandled exception occurred",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "request_id": request_id,
                "timestamp": time.time()
            }
        )


def setup_middleware(app):
    """Setup all middleware for the FastAPI application."""
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add TrustedHost middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    # Add custom metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Add request ID middleware
    app.add_middleware(RequestIDMiddleware)
    
    # Add global exception handler
    app.add_exception_handler(Exception, GlobalExceptionHandler.handle_exception)
    
    logger.info("All middleware configured successfully")


def get_cors_middleware_config():
    """Get CORS middleware configuration."""
    return {
        "allow_origins": ["*"],  # Configure appropriately for production
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }


def get_trusted_host_middleware_config():
    """Get TrustedHost middleware configuration."""
    return {
        "allowed_hosts": ["*"]  # Configure appropriately for production
    }


def create_request_id() -> str:
    """Create a unique request ID."""
    return str(uuid.uuid4())


def log_request_info(request: Request, response: Response, duration: float):
    """Log request information."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Request processed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
