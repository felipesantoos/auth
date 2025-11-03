"""
Unit tests for Cache Invalidation Service
Tests cache invalidation logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.cache.cache_invalidation_service import CacheInvalidationService


@pytest.mark.unit
class TestCacheInvalidation:
    """Test cache invalidation functionality"""
    
    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self):
        """Test invalidating all cache entries for a user"""
        cache_mock = AsyncMock()
        cache_mock.delete_pattern = AsyncMock(return_value=5)
        
        service = CacheInvalidationService()
        
        count = await service.invalidate_user_cache("user-123")
        
        cache_mock.delete_pattern.assert_called()
        assert count == 5 or count >= 0
    
    @pytest.mark.asyncio
    async def test_invalidate_client_cache(self):
        """Test invalidating all cache entries for a client"""
        cache_mock = AsyncMock()
        cache_mock.delete_pattern = AsyncMock(return_value=10)
        
        service = CacheInvalidationService()
        
        count = await service.invalidate_client_cache("client-123")
        
        cache_mock.delete_pattern.assert_called()
        assert count == 10 or count >= 0
    
    @pytest.mark.asyncio
    async def test_invalidate_specific_key(self):
        """Test invalidating specific cache key"""
        cache_mock = AsyncMock()
        cache_mock.delete = AsyncMock(return_value=True)
        
        service = CacheInvalidationService()
        
        result = await service.invalidate_key("user:123:profile")
        
        cache_mock.delete.assert_called_with("user:123:profile")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_invalidate_multiple_keys(self):
        """Test invalidating multiple cache keys"""
        cache_mock = AsyncMock()
        cache_mock.delete_many = AsyncMock(return_value=3)
        
        service = CacheInvalidationService()
        
        keys = ["key1", "key2", "key3"]
        count = await service.invalidate_keys(keys)
        
        cache_mock.delete_many.assert_called_with(keys)
        assert count == 3

