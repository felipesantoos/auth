"""
Unit tests for HTTPS Redirect Middleware
Tests HTTPS enforcement in production
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from starlette.responses import RedirectResponse, Response

from app.api.middlewares.https_redirect_middleware import HTTPSRedirectMiddleware


@pytest.mark.unit
class TestHTTPSRedirectMiddleware:
    """Test HTTPS redirect middleware"""

    @pytest.mark.asyncio
    @patch('app.api.middlewares.https_redirect_middleware.settings')
    async def test_allows_https_in_production(self, mock_settings):
        """Should allow HTTPS requests in production"""
        mock_settings.environment = "production"
        
        mock_app = Mock()
        middleware = HTTPSRedirectMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.scheme = "https"
        request.url.path = "/api/users"
        
        call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(request, call_next)
        
        # Should call next (not redirect)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    @patch('app.api.middlewares.https_redirect_middleware.settings')
    async def test_allows_http_in_development(self, mock_settings):
        """Should allow HTTP in development"""
        mock_settings.environment = "development"
        
        mock_app = Mock()
        middleware = HTTPSRedirectMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.scheme = "http"
        
        call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(request, call_next)
        
        # Should call next (not redirect)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.api.middlewares.https_redirect_middleware.settings')
    async def test_adds_hsts_header_in_production(self, mock_settings):
        """Should add HSTS header in production"""
        mock_settings.environment = "production"
        
        mock_app = Mock()
        middleware = HTTPSRedirectMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.url.scheme = "https"
        
        response = Response()
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        # Should add HSTS header
        assert "Strict-Transport-Security" in result.headers


@pytest.mark.unit
class TestHTTPSRedirectBehavior:
    """Test HTTPS redirect behavior"""

    @pytest.mark.asyncio
    @patch('app.api.middlewares.https_redirect_middleware.settings')
    async def test_middleware_exists(self, mock_settings):
        """Should be able to create middleware instance"""
        mock_settings.environment = "production"
        
        mock_app = Mock()
        middleware = HTTPSRedirectMiddleware(app=mock_app)
        
        assert middleware is not None
        assert hasattr(middleware, 'dispatch')

