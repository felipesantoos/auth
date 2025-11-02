"""
Unit tests for API Key Middleware
Tests API key authentication logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from app.api.middlewares.api_key_middleware import ApiKeyMiddleware


@pytest.mark.unit
class TestApiKeyMiddleware:
    """Test API key middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_api_key_allows_request(self):
        """Test valid API key allows request"""
        request_mock = Mock()
        request_mock.headers = {"X-API-Key": "valid_api_key_123"}
        
        call_next_mock = AsyncMock(return_value=Mock(status_code=200))
        
        middleware = ApiKeyMiddleware(Mock())
        
        with patch('app.api.middlewares.api_key_middleware.verify_api_key') as mock_verify:
            mock_verify.return_value = {
                "user_id": "user-123",
                "scopes": ["read:user", "write:user"]
            }
            
            response = await middleware.dispatch(request_mock, call_next_mock)
            
            assert response.status_code == 200
            call_next_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(self):
        """Test missing API key returns 401"""
        request_mock = Mock()
        request_mock.headers = {}
        
        middleware = ApiKeyMiddleware(Mock())
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request_mock, AsyncMock())
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self):
        """Test invalid API key returns 401"""
        request_mock = Mock()
        request_mock.headers = {"X-API-Key": "invalid_key"}
        
        middleware = ApiKeyMiddleware(Mock())
        
        with patch('app.api.middlewares.api_key_middleware.verify_api_key') as mock_verify:
            mock_verify.return_value = None  # Invalid key
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request_mock, AsyncMock())
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_revoked_api_key_returns_401(self):
        """Test revoked API key returns 401"""
        request_mock = Mock()
        request_mock.headers = {"X-API-Key": "revoked_key"}
        
        middleware = ApiKeyMiddleware(Mock())
        
        with patch('app.api.middlewares.api_key_middleware.verify_api_key') as mock_verify:
            mock_verify.side_effect = Exception("API key revoked")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request_mock, AsyncMock())
            
            assert exc_info.value.status_code == 401

