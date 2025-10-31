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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Request/Response Logging
from app.api.middlewares.logging_middleware import LoggingMiddleware
app.add_middleware(LoggingMiddleware)

# Register custom exception handlers
from app.api.middlewares.exception_handler import register_exception_handlers
register_exception_handlers(app)


# Global exception handler (fallback for uncaught exceptions)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if not settings.debug else str(exc)
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


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
from app.api.routes import client_routes
from app.api.routes import auth_routes

# Register routers
logger.info("Registering API routes...")

# Client Management (admin only)
app.include_router(client_routes.router)

# Authentication
app.include_router(auth_routes.router)

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

