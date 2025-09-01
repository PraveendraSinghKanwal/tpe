import logging
import sys
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory

from app.config import settings


def setup_logging() -> None:
    """Setup structured logging configuration."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request_info(request_id: str, method: str, path: str, **kwargs: Any) -> None:
    """Log request information."""
    logger = get_logger("request")
    logger.info(
        "Request processed",
        request_id=request_id,
        method=method,
        path=path,
        **kwargs
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log error information."""
    logger = get_logger("error")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True,
    )
