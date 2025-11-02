"""
Auth System API - Main Application Entry Point
FastAPI application with hexagonal architecture
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging

from config import settings
from config.logging_config import setup_logging
from infra.database import init_database, close_database
from infra.redis import init_redis, close_redis
from infra.redis.redis_pubsub import init_pubsub, close_pubsub, get_pubsub
import asyncio

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
        
        # Initialize Redis Pub/Sub
        logger.info("Initializing Redis Pub/Sub...")
        redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        if settings.redis_password:
            redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        
        pubsub = await init_pubsub(redis_url)
        
        # Subscribe to channels
        await pubsub.subscribe(
            "notifications",
            "cache_invalidation",
            "system_events"
        )
        
        # Register event handlers
        from app.api.websockets.connection_manager import manager
        
        @pubsub.on_message("notifications")
        async def handle_notification(data: dict):
            """Broadcast notification via WebSocket."""
            user_id = data.get("user_id")
            notification = data.get("notification")
            
            if user_id and notification:
                await manager.send_to_user(
                    message={
                        "type": "notification",
                        "notification": notification
                    },
                    user_id=user_id
                )
        
        @pubsub.on_message("cache_invalidation")
        async def handle_cache_invalidation(data: dict):
            """Handle cache invalidation events."""
            cache_key = data.get("key")
            logger.info(f"Cache invalidation event: {cache_key}")
            # In production, invalidate cache here
        
        @pubsub.on_message("system_events")
        async def handle_system_event(data: dict):
            """Handle system-wide events."""
            event_type = data.get("type")
            logger.info(f"System event: {event_type}")
        
        # Start listening for Pub/Sub messages in background
        asyncio.create_task(pubsub.listen())
        logger.info("Redis Pub/Sub initialized and listening")
        
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
        await close_pubsub()
        await close_database()
        await close_redis()
        logger.info("Auth System API shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application with enhanced OpenAPI documentation
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
# 🔐 Auth System API

Sistema completo de autenticação e autorização multi-tenant com suporte a múltiplos métodos de autenticação.

## ✨ Features

* **🔑 Autenticação Multi-Método**
  - Email/Password tradicional
  - OAuth2 (Google, GitHub, etc.)
  - Passwordless (Magic Links)
  - WebAuthn (FIDO2)
  - SSO/SAML
  
* **🛡️ Segurança Avançada**
  - MFA/2FA (TOTP, Backup Codes)
  - Session Management multi-device
  - Rate Limiting distribuído (Redis)
  - Account Lockout (brute-force protection)
  - Audit Logging completo
  
* **👥 Multi-Tenant**
  - Isolamento por cliente/tenant
  - API Keys por cliente
  - Subdomain routing
  
* **📊 Features Empresariais**
  - GDPR Compliance (data export/deletion)
  - Email tracking & A/B testing
  - File upload com chunked support
  - Real-time WebSocket communication
  - Fine-grained permissions

## 📈 Rate Limits

* **Autenticado**: 1000 requests/hora
* **Anônimo**: 60 requests/minuto
* **Login**: 5 tentativas/minuto
* **Registro**: 3 registros/minuto

## 🔒 Autenticação

Este API suporta múltiplos métodos de autenticação:

1. **Bearer Token (JWT)**: Header `Authorization: Bearer <token>`
2. **API Key**: Header `X-API-Key: <key>` 
3. **Cookies** (Web): `access_token` e `refresh_token` (httpOnly)

## 📝 Versionamento

API suporta versionamento via:
- **URL** (preferido): `/api/v1/auth/login`
- **Header**: `X-API-Version: 1.0`

Versão atual: **v1**

## ❌ Códigos de Erro

* `400` - Bad Request (dados inválidos)
* `401` - Unauthorized (autenticação requerida)
* `403` - Forbidden (sem permissão)
* `404` - Not Found (recurso não encontrado)
* `409` - Conflict (conflito, ex: email já existe)
* `422` - Unprocessable Entity (validação falhou)
* `429` - Too Many Requests (rate limit excedido)
* `500` - Internal Server Error (erro no servidor)
* `503` - Service Unavailable (serviço indisponível)

## 🆘 Suporte

* **Documentação**: https://docs.example.com
* **Status**: https://status.example.com
* **Email**: support@example.com
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    terms_of_service="https://example.com/terms",
    contact={
        "name": "Auth System Support",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)


def custom_openapi():
    """
    Customize OpenAPI schema with servers, security schemes, and examples.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # Add multiple servers (production, staging, development)
    openapi_schema["servers"] = [
        {
            "url": settings.api_url if hasattr(settings, 'api_url') else "https://api.example.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.example.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication. Obtenha o token via `/api/v1/auth/login` ou `/api/v1/auth/register`."
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key authentication. Obtenha uma API key via painel de administração."
        },
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "Cookie-based authentication (usado por clientes web)."
        }
    }
    
    # Add global security requirement (optional - endpoints can override)
    # openapi_schema["security"] = [
    #     {"BearerAuth": []},
    #     {"ApiKeyAuth": []},
    #     {"CookieAuth": []}
    # ]
    
    # Add custom extensions
    openapi_schema["x-logo"] = {
        "url": "https://example.com/logo.png",
        "altText": "Auth System Logo"
    }
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "Endpoints de autenticação: login, registro, logout, refresh token"
        },
        {
            "name": "MFA",
            "description": "Multi-Factor Authentication (2FA/TOTP)"
        },
        {
            "name": "Sessions",
            "description": "Gerenciamento de sessões multi-device"
        },
        {
            "name": "OAuth2",
            "description": "Autenticação via providers externos (Google, GitHub, etc.)"
        },
        {
            "name": "Passwordless Auth",
            "description": "Autenticação sem senha (Magic Links)"
        },
        {
            "name": "WebAuthn",
            "description": "Autenticação FIDO2/WebAuthn (biometria, security keys)"
        },
        {
            "name": "SSO",
            "description": "Single Sign-On e SAML"
        },
        {
            "name": "Clients",
            "description": "Gerenciamento de clientes/tenants (admin only)"
        },
        {
            "name": "Permissions",
            "description": "Sistema de permissões fine-grained"
        },
        {
            "name": "API Keys",
            "description": "Gerenciamento de API keys"
        },
        {
            "name": "User Profile",
            "description": "Perfil do usuário e configurações"
        },
        {
            "name": "GDPR Compliance",
            "description": "Compliance GDPR: export/delete de dados"
        },
        {
            "name": "Audit",
            "description": "Audit logs e histórico de eventos"
        },
        {
            "name": "File Upload",
            "description": "Upload de arquivos com suporte a chunked upload"
        },
        {
            "name": "Health",
            "description": "Health checks para monitoramento"
        },
        {
            "name": "Monitoring",
            "description": "Métricas Prometheus"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set custom OpenAPI schema
app.openapi = custom_openapi


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

# Configure Response Compression (Brotli + gzip fallback)
# Brotli offers 15-20% better compression than gzip
from brotli_asgi import BrotliMiddleware
app.add_middleware(
    BrotliMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
    quality=4,  # 0-11, quality 4 is good balance for dynamic content
    # gzip_fallback=True is default - automatically falls back to gzip if client doesn't support brotli
)

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
from app.api.routes import sse_routes
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

# Real-Time Communication
app.include_router(websocket_routes.router)
app.include_router(sse_routes.router)

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

