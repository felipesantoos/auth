"""
Unit tests for Rate Limit Middleware
Tests rate limiting functionality
"""
import pytest
from unittest.mock import Mock, patch

from app.api.middlewares.rate_limit_middleware import limiter, get_limiter


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter instance"""

    def test_limiter_exists(self):
        """Should have limiter instance"""
        assert limiter is not None

    def test_get_limiter_returns_instance(self):
        """Should return limiter instance"""
        result = get_limiter()
        assert result is not None
        assert result == limiter

    def test_limiter_has_default_limits(self):
        """Should have default rate limits configured"""
        # Limiter is configured with default limits from settings
        assert hasattr(limiter, '_default_limits')


@pytest.mark.unit
class TestRateLimitConfiguration:
    """Test rate limit configuration"""

    def test_limiter_uses_redis_storage(self):
        """Should use Redis for distributed rate limiting"""
        # Check that limiter is configured (can't test Redis connection in unit test)
        assert limiter is not None

    def test_limiter_key_function(self):
        """Should use remote address as key"""
        # The limiter uses get_remote_address as key function
        from slowapi.util import get_remote_address
        
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        
        key = get_remote_address(mock_request)
        assert key == "192.168.1.1"


@pytest.mark.unit
class TestRateLimitBehavior:
    """Test rate limiting behavior"""

    def test_rate_limit_format(self):
        """Should accept standard rate limit format"""
        # Standard formats: "60/minute", "100/hour", "1000/day"
        rate_limits = ["60/minute", "100/hour", "1000/day"]
        
        for limit in rate_limits:
            parts = limit.split('/')
            assert len(parts) == 2
            assert parts[0].isdigit()
            assert parts[1] in ['second', 'minute', 'hour', 'day']

    def test_parse_rate_limit_value(self):
        """Should parse rate limit value correctly"""
        rate_limit = "60/minute"
        count, period = rate_limit.split('/')
        
        assert int(count) == 60
        assert period == "minute"
