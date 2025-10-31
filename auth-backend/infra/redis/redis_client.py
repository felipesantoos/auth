"""
Redis Client Configuration
Used for caching, sessions, and rate limiting
"""
import redis.asyncio as redis
from config.settings import settings
from typing import Optional


class RedisClient:
    """Async Redis client wrapper"""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    async def get_client(cls) -> redis.Redis:
        """Get or create Redis client instance"""
        if cls._instance is None:
            redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            if settings.redis_password:
                redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            
            cls._instance = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
            )
        return cls._instance
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


async def get_redis_client() -> redis.Redis:
    """Dependency for getting Redis client"""
    return await RedisClient.get_client()


async def init_redis():
    """Initialize Redis connection"""
    await RedisClient.get_client()


async def close_redis():
    """Close Redis connection"""
    await RedisClient.close()

