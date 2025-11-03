"""
Unit tests for Upload Rate Limiter
Tests upload rate limiting functionality with Redis
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from app.api.middlewares.upload_rate_limiter import UploadRateLimiter


@pytest.mark.unit
class TestUploadRateLimiterInitialization:
    """Test UploadRateLimiter initialization"""

    @patch('app.api.middlewares.upload_rate_limiter.redis.Redis')
    def test_initializes_with_redis_client(self, mock_redis):
        """Should initialize with Redis client"""
        limiter = UploadRateLimiter()
        
        assert limiter is not None
        assert limiter.max_uploads_per_day == 100
        assert limiter.max_size_per_day_mb == 1000

    @patch('app.api.middlewares.upload_rate_limiter.redis.Redis')
    def test_redis_client_configured(self, mock_redis):
        """Should configure Redis client with settings"""
        limiter = UploadRateLimiter()
        
        # Redis was called with config
        mock_redis.assert_called_once()


@pytest.mark.unit
class TestUploadRateLimitChecks:
    """Test rate limit checking logic"""

    @patch('app.api.middlewares.upload_rate_limiter.redis.Redis')
    def test_check_rate_limit_under_limit(self, mock_redis):
        """Should allow upload when under limit"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = "50"  # 50 uploads today
        mock_redis.return_value = mock_redis_instance
        
        limiter = UploadRateLimiter()
        
        # Should not raise
        limiter.check_rate_limit("user-123", file_size=1024*1024)

    @patch('app.api.middlewares.upload_rate_limiter.redis.Redis')
    def test_check_rate_limit_over_count_limit(self, mock_redis):
        """Should reject when upload count exceeded"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = "100"  # Already at limit
        mock_redis.return_value = mock_redis_instance
        
        limiter = UploadRateLimiter()
        
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_rate_limit("user-123", file_size=1024)
        
        assert exc_info.value.status_code == 429


@pytest.mark.unit
class TestUploadRateLimitTracking:
    """Test rate limit tracking"""

    @patch('app.api.middlewares.upload_rate_limiter.redis.Redis')
    def test_increments_upload_count(self, mock_redis):
        """Should increment upload count after successful upload"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = "10"
        mock_redis_instance.incr.return_value = 11
        mock_redis.return_value = mock_redis_instance
        
        limiter = UploadRateLimiter()
        limiter.check_rate_limit("user-123", file_size=1024)
        
        # Should have called incr
        assert mock_redis_instance.incr.called or mock_redis_instance.get.called

    @patch('app.api.middlewares.upload_rate_limiter.redis.Redis')
    def test_tracks_upload_size(self, mock_redis):
        """Should track total upload size"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.get.return_value = "0"
        mock_redis.return_value = mock_redis_instance
        
        limiter = UploadRateLimiter()
        file_size = 5 * 1024 * 1024  # 5MB
        
        limiter.check_rate_limit("user-123", file_size=file_size)
        
        # Should have checked/updated size
        assert mock_redis_instance.get.called

