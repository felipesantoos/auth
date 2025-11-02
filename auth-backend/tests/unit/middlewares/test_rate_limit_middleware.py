"""
Unit tests for Rate Limit Middleware
Tests rate limiting logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from app.api.middlewares.rate_limit_middleware import RateLimitMiddleware


@pytest.mark.unit
class TestRateLimitMiddleware:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_request_under_limit_allowed(self):
        """Test request under rate limit is allowed"""
        request_mock = Mock()
        request_mock.client.host = "1.2.3.4"
        request_mock.url.path = "/api/auth/login"
        
        call_next_mock = AsyncMock(return_value=Mock(status_code=200))
        
        middleware = RateLimitMiddleware(Mock())
        
        with patch('app.api.middlewares.rate_limit_middleware.check_rate_limit') as mock_check:
            mock_check.return_value = True  # Under limit
            
            response = await middleware.dispatch(request_mock, call_next_mock)
            
            assert response.status_code == 200
            call_next_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_over_limit_blocked(self):
        """Test request over rate limit is blocked"""
        request_mock = Mock()
        request_mock.client.host = "1.2.3.4"
        request_mock.url.path = "/api/auth/login"
        
        middleware = RateLimitMiddleware(Mock())
        
        with patch('app.api.middlewares.rate_limit_middleware.check_rate_limit') as mock_check:
            mock_check.return_value = False  # Over limit
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request_mock, AsyncMock())
            
            assert exc_info.value.status_code == 429
    
    @pytest.mark.asyncio
    async def test_different_ips_tracked_separately(self):
        """Test different IPs are tracked separately"""
        middleware = RateLimitMiddleware(Mock())
        
        request1 = Mock()
        request1.client.host = "1.2.3.4"
        request1.url.path = "/api/test"
        
        request2 = Mock()
        request2.client.host = "5.6.7.8"
        request2.url.path = "/api/test"
        
        call_next = AsyncMock(return_value=Mock(status_code=200))
        
        with patch('app.api.middlewares.rate_limit_middleware.check_rate_limit') as mock_check:
            mock_check.return_value = True
            
            await middleware.dispatch(request1, call_next)
            await middleware.dispatch(request2, call_next)
            
            # Should check limit for each IP
            assert mock_check.call_count == 2

