"""
Cache Warming Tasks
Background tasks for preloading frequently accessed data
"""
import logging
import asyncio
from typing import List

from infra.celery.celery_app import celery_app
from infra.redis.cache_service import CacheService

logger = logging.getLogger(__name__)


@celery_app.task(name='warm_popular_cache')
def warm_popular_cache():
    """
    Warm cache with frequently accessed data.
    
    This task should run periodically (e.g., every 6 hours)
    to ensure popular data is always available in cache.
    """
    try:
        logger.info("[Celery] Starting cache warming task")
        
        # Run async cache warming
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_warm_cache_async())
        loop.close()
        
        logger.info(f"[Celery] Cache warming completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Cache warming failed: {e}", exc_info=True)
        raise


async def _warm_cache_async():
    """
    Async implementation of cache warming.
    
    Preloads:
    - Popular user profiles
    - Active client configurations
    - Frequently accessed settings
    """
    cache = CacheService()
    warmed_items = 0
    
    try:
        # Import here to avoid circular imports
        from infra.database.database import AsyncSessionLocal
        from infra.database.repositories.app_user_repository import AppUserRepository
        from infra.database.repositories.client_repository import ClientRepository
        
        async with AsyncSessionLocal() as session:
            # Warm active clients cache
            client_repo = ClientRepository(session)
            active_clients = await client_repo.find_all()
            
            for client in active_clients[:10]:  # Top 10 clients
                cache_key = f"client:{client.id}"
                await cache.set(
                    cache_key,
                    {
                        "id": client.id,
                        "name": client.name,
                        "subdomain": client.subdomain,
                        "is_active": client.is_active
                    },
                    ttl=3600  # 1 hour
                )
                warmed_items += 1
            
            logger.info(f"[Cache Warming] Warmed {warmed_items} client entries")
        
        return {
            "status": "success",
            "items_warmed": warmed_items
        }
    
    except Exception as e:
        logger.error(f"[Cache Warming] Error: {e}", exc_info=True)
        return {
            "status": "failed",
            "items_warmed": warmed_items,
            "error": str(e)
        }


@celery_app.task(name='warm_user_cache')
def warm_user_cache(user_ids: List[str]):
    """
    Warm cache for specific users.
    
    Useful after bulk operations or system updates.
    
    Args:
        user_ids: List of user IDs to warm cache for
    """
    try:
        logger.info(f"[Celery] Warming cache for {len(user_ids)} users")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_warm_user_cache_async(user_ids))
        loop.close()
        
        return result
    
    except Exception as e:
        logger.error(f"[Celery] User cache warming failed: {e}", exc_info=True)
        raise


async def _warm_user_cache_async(user_ids: List[str]):
    """Async implementation of user cache warming"""
    from infra.database.database import AsyncSessionLocal
    from infra.database.repositories.app_user_repository import AppUserRepository
    
    cache = CacheService()
    warmed = 0
    
    async with AsyncSessionLocal() as session:
        user_repo = AppUserRepository(session)
        
        for user_id in user_ids:
            try:
                user = await user_repo.find_by_id(user_id)
                if user:
                    cache_key = f"user:{user_id}"
                    await cache.set(
                        cache_key,
                        {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "name": user.name,
                            "role": user.role.value
                        },
                        ttl=1800  # 30 minutes
                    )
                    warmed += 1
            except Exception as e:
                logger.warning(f"Failed to warm cache for user {user_id}: {e}")
                continue
    
    logger.info(f"[Cache Warming] Warmed {warmed}/{len(user_ids)} user entries")
    
    return {
        "status": "success",
        "requested": len(user_ids),
        "warmed": warmed
    }


@celery_app.task(name='clear_expired_cache')
def clear_expired_cache():
    """
    Clear expired cache entries.
    
    Note: Redis automatically expires keys with TTL,
    but this can be used for additional cleanup if needed.
    """
    try:
        logger.info("[Celery] Clearing expired cache entries")
        
        # Most cleanup is automatic with Redis TTL
        # This task can be extended for custom cleanup logic
        
        return {
            "status": "success",
            "message": "Expired cache cleared (automatic via Redis TTL)"
        }
    
    except Exception as e:
        logger.error(f"[Celery] Cache cleanup failed: {e}", exc_info=True)
        raise

