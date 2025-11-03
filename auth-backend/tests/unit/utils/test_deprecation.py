"""
Unit tests for API Deprecation Utilities
Tests deprecation decorators and middleware
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Response, Request
from datetime import datetime

from app.api.utils.deprecation import (
    deprecated_endpoint,
    deprecation_middleware
)


@pytest.mark.unit
class TestDeprecatedEndpointDecorator:
    """Test deprecated endpoint decorator"""

    @pytest.mark.asyncio
    async def test_decorator_adds_headers(self):
        """Should add deprecation headers to response"""
        @deprecated_endpoint(
            deprecation_date="2024-01-01",
            sunset_date="2024-06-01",
            alternative="/api/v2/endpoint"
        )
        async def test_endpoint(response: Response):
            return {"data": "test"}
        
        response = Response()
        result = await test_endpoint(response=response)
        
        assert "Deprecation" in response.headers
        assert "Sunset" in response.headers
        assert "Link" in response.headers
        assert "X-API-Warn" in response.headers

    @pytest.mark.asyncio
    async def test_decorator_sets_dates(self):
        """Should set correct deprecation and sunset dates"""
        @deprecated_endpoint(
            deprecation_date="2024-01-01",
            sunset_date="2024-12-31",
            alternative="/new-endpoint"
        )
        async def test_endpoint(response: Response):
            return {}
        
        response = Response()
        await test_endpoint(response=response)
        
        assert response.headers["Deprecation"] == "2024-01-01"
        assert response.headers["Sunset"] == "2024-12-31"

    @pytest.mark.asyncio
    async def test_decorator_sets_alternative_link(self):
        """Should set Link header with alternative"""
        @deprecated_endpoint(
            deprecation_date="2024-01-01",
            sunset_date="2024-12-31",
            alternative="/api/v2/users"
        )
        async def test_endpoint(response: Response):
            return {}
        
        response = Response()
        await test_endpoint(response=response)
        
        link_header = response.headers["Link"]
        assert "/api/v2/users" in link_header
        assert 'rel="alternate"' in link_header


@pytest.mark.unit
class TestDeprecationMessage:
    """Test deprecation message generation"""

    @pytest.mark.asyncio
    async def test_default_message(self):
        """Should generate default deprecation message"""
        @deprecated_endpoint(
            deprecation_date="2024-01-01",
            sunset_date="2024-06-01",
            alternative="/new-endpoint"
        )
        async def test_endpoint(response: Response):
            return {}
        
        response = Response()
        await test_endpoint(response=response)
        
        warning = response.headers["X-API-Warn"]
        assert "deprecated" in warning.lower()
        assert "2024-01-01" in warning
        assert "2024-06-01" in warning

    @pytest.mark.asyncio
    async def test_custom_message(self):
        """Should use custom deprecation message"""
        custom_msg = "Please migrate to the new API"
        
        @deprecated_endpoint(
            deprecation_date="2024-01-01",
            sunset_date="2024-06-01",
            alternative="/new-endpoint",
            message=custom_msg
        )
        async def test_endpoint(response: Response):
            return {}
        
        response = Response()
        await test_endpoint(response=response)
        
        warning = response.headers["X-API-Warn"]
        assert custom_msg in warning


@pytest.mark.unit
class TestDeprecationMiddleware:
    """Test deprecation middleware"""

    @pytest.mark.asyncio
    async def test_middleware_adds_headers(self):
        """Should add deprecation headers via middleware"""
        middleware = deprecation_middleware(
            deprecation_date="2024-01-01",
            sunset_date="2024-12-31"
        )
        
        request = Mock(spec=Request)
        response = Response()
        
        async def call_next(req):
            return response
        
        result = await middleware(request, call_next)
        
        assert "Deprecation" in result.headers
        assert "Sunset" in result.headers

    @pytest.mark.asyncio
    async def test_middleware_preserves_response(self):
        """Should preserve original response"""
        middleware = deprecation_middleware(
            deprecation_date="2024-01-01",
            sunset_date="2024-12-31"
        )
        
        request = Mock(spec=Request)
        response = Response(content="test", status_code=200)
        
        async def call_next(req):
            return response
        
        result = await middleware(request, call_next)
        
        assert result.status_code == 200


@pytest.mark.unit
class TestDeprecationDocstring:
    """Test deprecation notice in docstring"""
