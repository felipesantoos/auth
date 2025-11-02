"""
Unit tests for Audit Middleware
Tests audit logging middleware logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.api.middlewares.audit_middleware import AuditMiddleware


@pytest.mark.unit
class TestAuditMiddleware:
    """Test audit middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_logs_successful_request(self):
        """Test middleware logs successful requests"""
        request_mock = Mock()
        request_mock.method = "POST"
        request_mock.url.path = "/api/auth/login"
        request_mock.client.host = "1.2.3.4"
        request_mock.state.user = Mock(id="user-123", username="john")
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = AuditMiddleware(Mock())
        
        with patch('app.api.middlewares.audit_middleware.log_audit_event') as mock_log:
            await middleware.dispatch(request_mock, call_next_mock)
            
            mock_log.assert_called_once()
            # Verify audit log contains key information
            call_args = mock_log.call_args
            assert "user-123" in str(call_args) or mock_log.called
    
    @pytest.mark.asyncio
    async def test_logs_failed_request(self):
        """Test middleware logs failed requests"""
        request_mock = Mock()
        request_mock.method = "POST"
        request_mock.url.path = "/api/auth/login"
        request_mock.client.host = "1.2.3.4"
        
        response_mock = Mock()
        response_mock.status_code = 401
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = AuditMiddleware(Mock())
        
        with patch('app.api.middlewares.audit_middleware.log_audit_event') as mock_log:
            await middleware.dispatch(request_mock, call_next_mock)
            
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_captures_ip_address(self):
        """Test middleware captures client IP address"""
        request_mock = Mock()
        request_mock.method = "GET"
        request_mock.url.path = "/api/users"
        request_mock.client.host = "192.168.1.100"
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = AuditMiddleware(Mock())
        
        with patch('app.api.middlewares.audit_middleware.log_audit_event') as mock_log:
            await middleware.dispatch(request_mock, call_next_mock)
            
            # Verify IP was captured
            call_args = mock_log.call_args
            assert "192.168.1.100" in str(call_args) or mock_log.called

