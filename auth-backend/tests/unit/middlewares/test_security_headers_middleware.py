"""
Unit tests for Security Headers Middleware
Tests security headers addition to responses
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from starlette.responses import Response

from app.api.middlewares.security_headers_middleware import SecurityHeadersMiddleware


@pytest.mark.unit
class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""

    @pytest.mark.asyncio
    async def test_middleware_initialization(self):
        """Should initialize security headers middleware"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        assert middleware is not None

    @pytest.mark.asyncio
    async def test_adds_content_security_policy(self):
        """Should add Content-Security-Policy header"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert "Content-Security-Policy" in result.headers

    @pytest.mark.asyncio
    async def test_adds_x_content_type_options(self):
        """Should add X-Content-Type-Options header"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert "X-Content-Type-Options" in result.headers
        assert result.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_adds_x_frame_options(self):
        """Should add X-Frame-Options header"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert "X-Frame-Options" in result.headers
        assert result.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_adds_x_xss_protection(self):
        """Should add X-XSS-Protection header"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert "X-XSS-Protection" in result.headers

    @pytest.mark.asyncio
    async def test_adds_referrer_policy(self):
        """Should add Referrer-Policy header"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert "Referrer-Policy" in result.headers

    @pytest.mark.asyncio
    async def test_adds_permissions_policy(self):
        """Should add Permissions-Policy header"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert "Permissions-Policy" in result.headers


@pytest.mark.unit
class TestSecurityHeadersPassthrough:
    """Test request passthrough"""

    @pytest.mark.asyncio
    async def test_passes_request_through(self):
        """Should pass request to next middleware"""
        mock_app = Mock()
        middleware = SecurityHeadersMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        
        response = Response(status_code=200, content=b"test")
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        call_next.assert_called_once_with(request)
        assert result.status_code == 200

