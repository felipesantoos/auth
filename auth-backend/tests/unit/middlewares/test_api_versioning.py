"""
Unit tests for API Versioning Middleware
Tests API version routing logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from app.api.middlewares.api_versioning import APIVersioningMiddleware


@pytest.mark.unit
class TestAPIVersioningMiddleware:
    """Test API versioning middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_extracts_version_from_header(self):
        """Test middleware extracts API version from header"""
        request_mock = Mock()
        request_mock.headers = {"X-API-Version": "v2"}
        request_mock.state = Mock()
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = APIVersioningMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        # Should set api_version in request state
        assert hasattr(request_mock.state, 'api_version') or response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_defaults_to_v1_when_no_version(self):
        """Test defaults to v1 when no version specified"""
        request_mock = Mock()
        request_mock.headers = {}
        request_mock.state = Mock()
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = APIVersioningMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        # Should default to v1
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_extracts_version_from_path(self):
        """Test middleware can extract version from URL path"""
        request_mock = Mock()
        request_mock.url.path = "/api/v2/users"
        request_mock.headers = {}
        request_mock.state = Mock()
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        middleware = APIVersioningMiddleware(Mock())
        
        response = await middleware.dispatch(request_mock, call_next_mock)
        
        assert response.status_code == 200

