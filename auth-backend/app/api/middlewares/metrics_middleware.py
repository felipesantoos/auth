"""
Prometheus Metrics Middleware
Tracks HTTP request metrics for monitoring and observability
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import logging

logger = logging.getLogger(__name__)


# Define Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP metrics with Prometheus.
    
    Tracks:
    - Request count by method, endpoint, and status
    - Request duration by method and endpoint
    - Request and response sizes
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and track metrics"""
        # Skip metrics collection for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Get request size
        request_size = int(request.headers.get('content-length', 0))
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Track failed requests
            duration = time.time() - start_time
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status='500'
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get response size (if available)
        response_size = 0
        if hasattr(response, 'body'):
            response_size = len(response.body) if response.body else 0
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(response.status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        if request_size > 0:
            http_request_size_bytes.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(request_size)
        
        if response_size > 0:
            http_response_size_bytes.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(response_size)
        
        # Add metrics header to response (for debugging)
        response.headers['X-Request-Duration'] = f"{duration:.3f}s"
        
        return response


def get_metrics() -> Response:
    """
    Generate Prometheus metrics endpoint response.
    
    Returns:
        Response with Prometheus metrics in text format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

