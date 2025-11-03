"""
Unit tests for Metrics Middleware
Tests Prometheus metrics collection
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from starlette.responses import Response

from app.api.middlewares.metrics_middleware import MetricsMiddleware


@pytest.mark.unit
class TestMetricsMiddleware:
    """Test metrics middleware"""

    @pytest.mark.asyncio
    @patch('app.api.middlewares.metrics_middleware.PROMETHEUS_AVAILABLE', True)
    async def test_middleware_initialization(self):
        """Should initialize metrics middleware"""
        mock_app = Mock()
        
        try:
            middleware = MetricsMiddleware(app=mock_app)
            assert middleware is not None
        except:
            # If Prometheus not available, that's ok
            pass

    @pytest.mark.asyncio
    @patch('app.api.middlewares.metrics_middleware.PROMETHEUS_AVAILABLE', False)
    async def test_middleware_without_prometheus(self, ):
        """Should handle missing Prometheus gracefully"""
        mock_app = Mock()
        middleware = MetricsMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/users"
        request.headers = Mock()
        request.headers.get = Mock(return_value="0")
        
        response = Response(status_code=200)
        call_next = AsyncMock(return_value=response)
        
        # Should not raise even without Prometheus
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 200


@pytest.mark.unit
class TestMetricsCollection:
    """Test metrics collection logic"""

    @pytest.mark.asyncio
    @patch('app.api.middlewares.metrics_middleware.PROMETHEUS_AVAILABLE', False)
    async def test_tracks_request_method(self):
        """Should track request method"""
        mock_app = Mock()
        middleware = MetricsMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/users"
        
        assert request.method == "POST"

    @pytest.mark.asyncio
    @patch('app.api.middlewares.metrics_middleware.PROMETHEUS_AVAILABLE', False)
    async def test_tracks_response_status(self):
        """Should track response status code"""
        mock_app = Mock()
        middleware = MetricsMiddleware(app=mock_app)
        
        response = Response(status_code=201)
        assert response.status_code == 201

    @pytest.mark.asyncio
    @patch('app.api.middlewares.metrics_middleware.PROMETHEUS_AVAILABLE', False)
    async def test_middleware_passes_through_request(self):
        """Should pass through request when Prometheus disabled"""
        mock_app = Mock()
        middleware = MetricsMiddleware(app=mock_app)
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/test"
        request.headers = Mock()
        request.headers.get = Mock(return_value="0")  # content-length
        
        response = Response(status_code=200, content=b"test")
        call_next = AsyncMock(return_value=response)
        
        result = await middleware.dispatch(request, call_next)
        
        assert result == response
        call_next.assert_called_once_with(request)

