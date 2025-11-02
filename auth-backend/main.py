"""
Auth System API - Main Application Entry Point
FastAPI application with hexagonal architecture
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from config.logging_config import setup_logging
from infra.database import init_database, close_database
from infra.redis import init_redis, close_redis

# Configure structured logging
setup_logging(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Auth System API...")
    logger.info(f"Environment: {settings.environment}")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize Redis
        logger.info("Initializing Redis connection...")
        await init_redis()
        logger.info("Redis initialized successfully")
        
        # Create uploads directory for local storage
        if settings.storage_provider == "local":
            import os
            from pathlib import Path
            uploads_dir = Path(settings.local_storage_path)
            uploads_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Uploads directory ensured: {uploads_dir}")
        
        logger.info("Auth System API started successfully!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth System API...")
    
    try:
        await close_database()
        await close_redis()
        logger.info("Auth System API shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-tenant Authentication and Authorization System",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Use property that converts string to list
    allow_credentials=True,
    # Métodos específicos ao invés de "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    # Headers específicos ao invés de "*"
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Client-ID",
        "X-Client-Subdomain",
        "X-Request-ID",
        "X-Client-Type",  # For dual-mode auth (web/mobile)
    ],
    # Expor headers úteis
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

# Configure Security Headers (OWASP Best Practices)
from app.api.middlewares.security_headers_middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure Request/Response Logging
from app.api.middlewares.logging_middleware import LoggingMiddleware
app.add_middleware(LoggingMiddleware)

# Configure Metrics Collection (Prometheus)
from app.api.middlewares.metrics_middleware import MetricsMiddleware
app.add_middleware(MetricsMiddleware)

# Configure Response Compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Configure API Versioning (Header-based)
from app.api.middlewares.api_versioning import APIVersionMiddleware
app.add_middleware(APIVersionMiddleware)

# HTTPS Redirect (Production only)
from app.api.middlewares.https_redirect_middleware import HTTPSRedirectMiddleware

if settings.environment == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("HTTPS redirect middleware enabled (production mode)")

# Configure Rate Limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.middlewares.rate_limit_middleware import limiter

# Add rate limiter to app state
app.state.limiter = limiter

# Add exception handler for rate limit errors
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register custom exception handlers
# This registers all domain exception handlers AND the global middleware
from app.api.middlewares.exception_handler import register_exception_handlers
register_exception_handlers(app)


# Note: Health check endpoints moved to app/api/routes/health_routes.py
# Basic /health, /health/ready, and /health/live endpoints are available


# Metrics endpoint for Prometheus
from app.api.middlewares.metrics_middleware import get_metrics

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Exposes application metrics in Prometheus format:
    - http_requests_total: Total HTTP requests by method, endpoint, status
    - http_request_duration_seconds: Request duration histogram
    - http_request_size_bytes: Request size histogram
    - http_response_size_bytes: Response size histogram
    """
    return get_metrics()


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Auth System API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Disabled in production",
    }


# Import and register routes
from app.api.routes import health_routes
from app.api.routes import websocket_routes
from app.api.routes import client_routes
from app.api.routes import auth_routes
from app.api.routes import oauth_routes
from app.api.routes import mfa_routes
from app.api.routes import session_routes
from app.api.routes import email_verification_routes
from app.api.routes import api_key_routes
from app.api.routes import passwordless_routes
from app.api.routes import audit_routes
from app.api.routes import gdpr_routes
from app.api.routes import webauthn_routes
from app.api.routes import sso_routes
from app.api.routes import permission_routes
from app.api.routes import profile_routes
from app.api.routes import email_tracking_routes
from app.api.routes import email_ab_test_routes
from app.api.routes.webhooks import email_webhooks
from app.api.routes import file_routes
from app.api.routes import serve_files_routes
from app.api.routes import chunked_upload_routes

# Register routers
logger.info("Registering API routes...")

# Health Checks & Monitoring
app.include_router(health_routes.router)

# WebSocket Real-Time Communication
app.include_router(websocket_routes.router)

# Client Management (admin only)
app.include_router(client_routes.router)

# Authentication (Basic)
app.include_router(auth_routes.router)

# OAuth2
app.include_router(oauth_routes.router)

# Advanced Auth Features
app.include_router(mfa_routes.router)
app.include_router(session_routes.router)
app.include_router(email_verification_routes.router)
app.include_router(api_key_routes.router)
app.include_router(passwordless_routes.router)
app.include_router(audit_routes.router)

# GDPR Compliance
app.include_router(gdpr_routes.router)

# Enterprise SSO Features
app.include_router(webauthn_routes.router)
app.include_router(sso_routes.router)

# Fine-Grained Access Control & User Profile
app.include_router(permission_routes.router)
app.include_router(profile_routes.router)

# Email Service (Tracking, A/B Testing & Webhooks)
app.include_router(email_tracking_routes.router)
app.include_router(email_ab_test_routes.router)
app.include_router(email_webhooks.router)

# File Upload & Storage
app.include_router(file_routes.router)
app.include_router(serve_files_routes.router)
app.include_router(chunked_upload_routes.router)

logger.info("All routes registered successfully")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level,
    )

