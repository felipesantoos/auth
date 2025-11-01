"""
Upload Rate Limiter Middleware
Redis-based rate limiting for file uploads
"""
from functools import wraps
from fastapi import HTTPException
from typing import Callable
import redis
from datetime import datetime, timedelta
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class UploadRateLimiter:
    """Rate limiter for file uploads using Redis."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True
        )
        self.max_uploads_per_day = 100
        self.max_size_per_day_mb = 1000
    
    def check_rate_limit(self, user_id: str, file_size: int = 0) -> None:
        """
        Check if user has exceeded rate limits.
        
        Args:
            user_id: User ID to check
            file_size: Size of file being uploaded (bytes)
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        count_key = f"upload_count:{user_id}:{today}"
        size_key = f"upload_size:{user_id}:{today}"
        
        # Get current counts
        upload_count = int(self.redis_client.get(count_key) or 0)
        upload_size = int(self.redis_client.get(size_key) or 0)
        
        # Check upload count limit
        if upload_count >= self.max_uploads_per_day:
            logger.warning(f"Upload count limit exceeded for user {user_id}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Daily upload limit of {self.max_uploads_per_day} files exceeded",
                    "retry_after": "24h"
                }
            )
        
        # Check total size limit
        file_size_mb = file_size / (1024 * 1024)
        total_size_mb = upload_size / (1024 * 1024)
        
        if total_size_mb + file_size_mb > self.max_size_per_day_mb:
            logger.warning(f"Upload size limit exceeded for user {user_id}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "SIZE_LIMIT_EXCEEDED",
                    "message": f"Daily upload size limit of {self.max_size_per_day_mb}MB exceeded",
                    "current_usage_mb": round(total_size_mb, 2),
                    "retry_after": "24h"
                }
            )
    
    def increment_usage(self, user_id: str, file_size: int) -> None:
        """
        Increment upload counters for user.
        
        Args:
            user_id: User ID
            file_size: Size of uploaded file (bytes)
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        count_key = f"upload_count:{user_id}:{today}"
        size_key = f"upload_size:{user_id}:{today}"
        
        # Increment counters
        self.redis_client.incr(count_key)
        self.redis_client.incrby(size_key, file_size)
        
        # Set expiration (24 hours + buffer)
        self.redis_client.expire(count_key, 90000)  # 25 hours
        self.redis_client.expire(size_key, 90000)
    
    def get_usage(self, user_id: str) -> dict:
        """Get current usage stats for user."""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        count_key = f"upload_count:{user_id}:{today}"
        size_key = f"upload_size:{user_id}:{today}"
        
        upload_count = int(self.redis_client.get(count_key) or 0)
        upload_size = int(self.redis_client.get(size_key) or 0)
        
        return {
            "uploads_today": upload_count,
            "max_uploads": self.max_uploads_per_day,
            "size_today_mb": round(upload_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size_per_day_mb,
            "remaining_uploads": max(0, self.max_uploads_per_day - upload_count),
            "remaining_size_mb": max(0, self.max_size_per_day_mb - (upload_size / (1024 * 1024)))
        }


# Singleton instance
_rate_limiter = UploadRateLimiter()


def upload_rate_limit(max_per_day: int = 100, max_size_per_day_mb: int = 1000):
    """
    Decorator for rate limiting file uploads.
    
    Args:
        max_per_day: Maximum uploads per day
        max_size_per_day_mb: Maximum total upload size per day (MB)
    
    Usage:
        @router.post("/upload")
        @upload_rate_limit(max_per_day=50, max_size_per_day_mb=500)
        async def upload_file(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by Depends)
            current_user = kwargs.get('current_user')
            
            if current_user:
                # Get file size if available
                file = kwargs.get('file')
                file_size = file.size if file and hasattr(file, 'size') else 0
                
                # Check rate limit
                _rate_limiter.max_uploads_per_day = max_per_day
                _rate_limiter.max_size_per_day_mb = max_size_per_day_mb
                _rate_limiter.check_rate_limit(current_user.id, file_size)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Increment usage after successful upload
                _rate_limiter.increment_usage(current_user.id, file_size)
                
                return result
            else:
                # No user, skip rate limiting
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_upload_rate_limiter() -> UploadRateLimiter:
    """Get rate limiter instance."""
    return _rate_limiter

