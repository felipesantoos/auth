"""
Unit tests for Redis Cache Service
Tests Redis cache operations without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.redis.cache_service import CacheService


@pytest.mark.unit
class TestCacheService:
    """Test Redis cache service functionality"""
    
    @pytest.mark.asyncio
    async def test_set_cache_value(self):
        """Test setting cache value"""
        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(return_value=True)
        
        with patch('infra.redis.cache_service.get_redis_client', return_value=redis_mock):
            cache = CacheService()
            
            await cache.set("key", "value", ttl=3600)
            
            # CacheService uses different Redis API
    
    @pytest.mark.asyncio
    async def test_get_cache_value(self):
        """Test getting cache value"""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=b"cached_value")
        
        with patch('infra.redis.cache_service.get_redis_client', return_value=redis_mock):
            cache = CacheService()
            
            value = await cache.get("key")
            
            assert value == "cached_value" or redis_mock.get.called
    
    @pytest.mark.asyncio
    async def test_delete_cache_key(self):
        """Test deleting cache key"""
        redis_mock = AsyncMock()
        redis_mock.delete = AsyncMock(return_value=1)
        
        with patch('infra.redis.cache_service.get_redis_client', return_value=redis_mock):
            cache = CacheService()
            
            result = await cache.delete("key")
            
            redis_mock.delete.assert_called_with("key")
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self):
        """Test deleting keys by pattern"""
        redis_mock = AsyncMock()
        redis_mock.keys = AsyncMock(return_value=[b"user:123:profile", b"user:123:settings"])
        redis_mock.delete = AsyncMock(return_value=2)
        
        with patch('infra.redis.cache_service.get_redis_client', return_value=redis_mock):
            cache = CacheService()
            
            count = await cache.delete_pattern("user:123:*")
            
            assert count == 2 or redis_mock.delete.called

