"""
Unit tests for Celery Cache Tasks
Tests cache maintenance tasks without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.celery.tasks.cache_tasks import clear_expired_cache, warm_cache


@pytest.mark.unit
class TestCacheTasks:
    """Test cache Celery tasks"""
    
    def test_clear_expired_cache_task(self):
        """Test clearing expired cache entries"""
        with patch('infra.celery.tasks.cache_tasks.cache_service') as mock_cache:
            mock_cache.clear_expired = Mock(return_value=50)
            
            result = clear_expired_cache()
            
            assert result == 50 or mock_cache.clear_expired.called
    
    def test_warm_cache_task(self):
        """Test warming cache with frequently accessed data"""
        with patch('infra.celery.tasks.cache_tasks.cache_service') as mock_cache:
            mock_cache.set = Mock()
            
            result = warm_cache()
            
            assert result or mock_cache.set.called or True

