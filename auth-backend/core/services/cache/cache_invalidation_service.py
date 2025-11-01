"""
Cache Invalidation Service
Provides structured cache invalidation patterns for the application
"""
from typing import List, Optional
import logging

from infra.redis.cache_service import CacheService

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """
    Service for managing cache invalidation.
    
    Provides centralized cache invalidation logic to ensure
    consistency when data changes in the database.
    """
    
    def __init__(self):
        self.cache = CacheService()
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """
        Invalidate all cache entries related to a user.
        
        Called when user data changes (profile update, role change, etc.)
        
        Args:
            user_id: User ID
            
        Returns:
            Number of keys deleted
        """
        patterns_to_delete = [
            f"user:{user_id}",
            f"user:*:{user_id}",
            f"profile:{user_id}",
            f"sessions:{user_id}:*",
            f"api_keys:{user_id}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns_to_delete:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated user cache", extra={
            "user_id": user_id,
            "keys_deleted": total_deleted
        })
        
        return total_deleted
    
    async def invalidate_client_cache(self, client_id: str) -> int:
        """
        Invalidate all cache entries related to a client (tenant).
        
        Called when client settings change.
        
        Args:
            client_id: Client ID
            
        Returns:
            Number of keys deleted
        """
        patterns_to_delete = [
            f"client:{client_id}",
            f"client:*:{client_id}",
            f"users:client:{client_id}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns_to_delete:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated client cache", extra={
            "client_id": client_id,
            "keys_deleted": total_deleted
        })
        
        return total_deleted
    
    async def invalidate_auth_cache(self, user_id: str) -> int:
        """
        Invalidate authentication-related cache for a user.
        
        Called when password changes, MFA is enabled/disabled, etc.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of keys deleted
        """
        patterns_to_delete = [
            f"auth:{user_id}:*",
            f"tokens:{user_id}:*",
            f"mfa:{user_id}:*",
            f"sessions:{user_id}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns_to_delete:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated auth cache", extra={
            "user_id": user_id,
            "keys_deleted": total_deleted
        })
        
        return total_deleted
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Generic pattern-based cache invalidation.
        
        Use with caution - prefer specific invalidation methods.
        
        Args:
            pattern: Redis key pattern (e.g., "user:*", "session:123:*")
            
        Returns:
            Number of keys deleted
        """
        deleted = await self.cache.delete_pattern(pattern)
        
        logger.info(f"Invalidated cache by pattern", extra={
            "pattern": pattern,
            "keys_deleted": deleted
        })
        
        return deleted
    
    async def invalidate_keys(self, keys: List[str]) -> int:
        """
        Invalidate specific cache keys.
        
        Args:
            keys: List of cache keys to delete
            
        Returns:
            Number of keys deleted
        """
        deleted = 0
        for key in keys:
            success = await self.cache.delete(key)
            if success:
                deleted += 1
        
        logger.info(f"Invalidated specific keys", extra={
            "keys_count": len(keys),
            "keys_deleted": deleted
        })
        
        return deleted
    
    async def invalidate_file_cache(self, file_id: str) -> int:
        """
        Invalidate file-related cache.
        
        Called when file metadata changes or file is deleted.
        
        Args:
            file_id: File ID
            
        Returns:
            Number of keys deleted
        """
        patterns_to_delete = [
            f"file:{file_id}",
            f"file:metadata:{file_id}",
            f"file:*:{file_id}",
        ]
        
        total_deleted = 0
        for pattern in patterns_to_delete:
            deleted = await self.cache.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated file cache", extra={
            "file_id": file_id,
            "keys_deleted": total_deleted
        })
        
        return total_deleted
    
    async def invalidate_session_cache(self, session_id: str) -> bool:
        """
        Invalidate a specific session cache.
        
        Called when session is logged out or expired.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session was deleted
        """
        key = f"session:{session_id}"
        success = await self.cache.delete(key)
        
        logger.info(f"Invalidated session cache", extra={
            "session_id": session_id,
            "success": success
        })
        
        return success

