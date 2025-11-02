"""
Unit tests for Security Headers Middleware
Tests security headers logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from app.api.middlewares.security_headers_middleware import SecurityHeadersMiddleware


@pytest.mark.unit
class TestSecurityHeadersMiddleware:
    """Test security headers middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_adds_security_headers(self):
        """Test middleware adds all required security headers"""
        request_mock = Mock()
        
        response_mock = Mock()
        response_mock.headers = {}
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = SecurityHeadersMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        # Check required security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Strict-Transport-Security" in response.headers
    
    @pytest.mark.asyncio
    async def test_adds_csp_header(self):
        """Test Content-Security-Policy header is added"""
        request_mock = Mock()
        
        response_mock = Mock()
        response_mock.headers = {}
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = SecurityHeadersMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        assert "Content-Security-Policy" in response.headers
    
    @pytest.mark.asyncio
    async def test_nosniff_header_value(self):
        """Test X-Content-Type-Options is set to nosniff"""
        request_mock = Mock()
        
        response_mock = Mock()
        response_mock.headers = {}
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = SecurityHeadersMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    @pytest.mark.asyncio
    async def test_frame_options_deny(self):
        """Test X-Frame-Options is set to DENY or SAMEORIGIN"""
        request_mock = Mock()
        
        response_mock = Mock()
        response_mock.headers = {}
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = SecurityHeadersMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        frame_option = response.headers.get("X-Frame-Options", "")
        assert frame_option in ["DENY", "SAMEORIGIN"]

