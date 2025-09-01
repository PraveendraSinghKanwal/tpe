from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time
from typing import Dict, Any

from app.config import settings

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

# LLM-specific metrics
LLM_REQUEST_COUNT = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['model', 'endpoint', 'status']
)

LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model', 'endpoint']
)

LLM_TOKEN_USAGE = Counter(
    'llm_tokens_total',
    'Total token usage',
    ['model', 'endpoint', 'token_type']
)


class MetricsMiddleware:
    """Middleware to collect HTTP request metrics."""
    
    def __init__(self):
        self.enabled = settings.enable_metrics
    
    async def __call__(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Increment active requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
            
            # Record successful request
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            
        except Exception as e:
            status = 500
            # Record failed request
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            raise
        finally:
            # Record request duration
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Decrement active requests
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
        
        return response


def record_llm_metrics(
    model: str,
    endpoint: str,
    duration: float,
    status: str = "success",
    prompt_tokens: int = None,
    completion_tokens: int = None,
    total_tokens: int = None
) -> None:
    """Record LLM-related metrics."""
    if not settings.enable_metrics:
        return
    
    LLM_REQUEST_COUNT.labels(model=model, endpoint=endpoint, status=status).inc()
    LLM_REQUEST_DURATION.labels(model=model, endpoint=endpoint).observe(duration)
    
    if prompt_tokens:
        LLM_TOKEN_USAGE.labels(model=model, endpoint=endpoint, token_type="prompt").inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKEN_USAGE.labels(model=model, endpoint=endpoint, token_type="completion").inc(completion_tokens)
    if total_tokens:
        LLM_TOKEN_USAGE.labels(model=model, endpoint=endpoint, token_type="total").inc(total_tokens)


async def metrics_endpoint() -> Response:
    """Endpoint to expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
