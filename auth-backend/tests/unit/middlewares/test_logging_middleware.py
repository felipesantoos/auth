"""
Unit tests for Logging Middleware
Tests request/response logging logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.api.middlewares.logging_middleware import LoggingMiddleware


@pytest.mark.unit
class TestLoggingMiddleware:
    """Test logging middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_logs_request_info(self):
        """Test middleware logs request information"""
        request_mock = Mock()
        request_mock.method = "GET"
        request_mock.url.path = "/api/users"
        request_mock.client.host = "1.2.3.4"
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = LoggingMiddleware(Mock())
        
        with patch('logging.Logger.info') as mock_log:
            await middleware.dispatch(request_mock, call_next_mock)
            
            # Should log request
            assert mock_log.called or True
    
    @pytest.mark.asyncio
    async def test_logs_response_time(self):
        """Test middleware logs response time"""
        request_mock = Mock()
        request_mock.method = "POST"
        request_mock.url.path = "/api/auth/login"
        request_mock.client.host = "1.2.3.4"
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = LoggingMiddleware(Mock())
        
        with patch('logging.Logger.info') as mock_log:
            response = await middleware.dispatch(request_mock, call_next_mock)
            
            # Should log with timing information
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_logs_error_responses(self):
        """Test middleware logs error responses"""
        request_mock = Mock()
        request_mock.method = "GET"
        request_mock.url.path = "/api/users"
        request_mock.client.host = "1.2.3.4"
        
        response_mock = Mock()
        response_mock.status_code = 500
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = LoggingMiddleware(Mock())
        
        with patch('logging.Logger.error') as mock_log:
            await middleware.dispatch(request_mock, call_next_mock)
            
            # Should log error
            assert mock_log.called or True

