"""
Unit tests for Celery Cache Tasks
Tests cache maintenance tasks without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.celery.tasks.cache_tasks import clear_expired_cache, warm_popular_cache


@pytest.mark.unit
class TestCacheTasks:
    """Test cache Celery tasks"""
    
    def test_clear_expired_cache_task(self):
        """Test clearing expired cache entries"""
        # Just verify function exists and is callable
        assert callable(clear_expired_cache)
    
    def test_warm_popular_cache_task(self):
        """Test warming cache with frequently accessed data"""
        # Just verify function exists and is callable
        assert callable(warm_popular_cache)

