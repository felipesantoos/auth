"""
Redis Cache Service
Provides caching functionality for frequently accessed data
"""
import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
from infra.redis.redis_client import get_redis_client
from core.interfaces.secondary.cache_service_interface import CacheServiceInterface

logger = logging.getLogger(__name__)


class CacheService(CacheServiceInterface):
    """
    Redis cache service for application data
    
    Provides caching with automatic serialization/deserialization
    """
    
    async def _get_redis(self):
        """Get Redis client"""
        return await get_redis_client()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            redis_client = await self._get_redis()
            value = await redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT", extra={"key": key})
                # Try to parse as JSON, fallback to string
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, return as string
                    return value
            logger.debug(f"Cache MISS", extra={"key": key})
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {str(e)}", extra={"key": key})
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or 3600  # 1 hour default
            redis_client = await self._get_redis()
            # If value is a simple string, store directly; otherwise JSON encode
            if isinstance(value, str):
                serialized = value
            else:
                serialized = json.dumps(value)
            await redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET", extra={"key": key, "ttl": ttl})
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {str(e)}", extra={"key": key})
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(key)
            logger.debug(f"Cache DELETE", extra={"key": key})
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error: {str(e)}", extra={"key": key})
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            redis_client = await self._get_redis()
            deleted = 0
            async for key in redis_client.scan_iter(match=pattern):
                await redis_client.delete(key)
                deleted += 1
            logger.info(f"Cache pattern DELETE", extra={"pattern": pattern, "deleted": deleted})
            return deleted
        except Exception as e:
            logger.warning(f"Cache pattern delete error: {str(e)}", extra={"pattern": pattern})
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all cache (use with caution!)"""
        try:
            redis_client = await self._get_redis()
            await redis_client.flushdb()
            logger.warning("Cache CLEARED - all keys deleted")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False


def cached(key_prefix: str, ttl: int = 3600):
    """
    Decorator for caching async function results
    
    Usage:
        @cached("bonds", ttl=3600)
        async def get_all_bonds():
            return await repository.find_all()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            
            # Try to get from cache
            cache = CacheService()
            cached_value = await cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Not in cache, execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

