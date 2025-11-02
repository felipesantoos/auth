"""
Health Check Endpoints
Advanced health checks for monitoring and orchestration
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from infra.database.database import get_db_session
from infra.redis.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health")
async def basic_health_check():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    return {
        "status": "healthy",
        "service": "auth-backend"
    }


@router.get("/health/ready")
async def readiness_check(session: AsyncSession = Depends(get_db_session)):
    """
    Readiness check - determines if service can handle traffic.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    
    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "database": "unknown",
        "redis": "unknown"
    }
    
    try:
        # Check database
        try:
            await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
            logger.debug("Database readiness check: OK")
        except Exception as db_error:
            checks["database"] = "failed"
            logger.error(f"Database readiness check failed: {db_error}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "checks": checks,
                    "error": "Database connection failed"
                }
            )
        
        # Check Redis
        try:
            cache = CacheService()
            redis_client = await cache._get_redis()
            await redis_client.ping()
            checks["redis"] = "ok"
            logger.debug("Redis readiness check: OK")
        except Exception as redis_error:
            checks["redis"] = "failed"
            logger.error(f"Redis readiness check failed: {redis_error}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "checks": checks,
                    "error": "Redis connection failed"
                }
            )
        
        # All checks passed
        return {
            "status": "ready",
            "checks": checks
        }
        
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "checks": checks,
                "error": str(e)
            }
        )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - determines if service is alive.
    
    Simple check that returns 200 if the process is running.
    Used by orchestrators to determine if service should be restarted.
    """
    return {
        "status": "alive"
    }

