"""
Unit tests for Auth Middleware
Tests authentication middleware logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from app.api.middlewares.auth_middleware import AuthMiddleware


@pytest.mark.unit
class TestAuthMiddleware:
    """Test authentication middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_token_allows_request(self):
        """Test valid JWT token allows request to proceed"""
        request_mock = Mock()
        request_mock.headers = {"Authorization": "Bearer valid_token_123"}
        
        call_next_mock = AsyncMock(return_value=Mock(status_code=200))
        
        middleware = AuthMiddleware(Mock())
        
        with patch('app.api.middlewares.auth_middleware.verify_token') as mock_verify:
            mock_verify.return_value = {"user_id": "user-123", "client_id": "client-123"}
            
            response = await middleware.dispatch(request_mock, call_next_mock)
            
            assert response.status_code == 200
            call_next_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_missing_token_returns_401(self):
        """Test missing authorization header returns 401"""
        request_mock = Mock()
        request_mock.headers = {}
        
        middleware = AuthMiddleware(Mock())
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request_mock, AsyncMock())
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self):
        """Test invalid JWT token returns 401"""
        request_mock = Mock()
        request_mock.headers = {"Authorization": "Bearer invalid_token"}
        
        middleware = AuthMiddleware(Mock())
        
        with patch('app.api.middlewares.auth_middleware.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request_mock, AsyncMock())
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self):
        """Test expired JWT token returns 401"""
        request_mock = Mock()
        request_mock.headers = {"Authorization": "Bearer expired_token"}
        
        middleware = AuthMiddleware(Mock())
        
        with patch('app.api.middlewares.auth_middleware.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Token expired")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request_mock, AsyncMock())
            
            assert exc_info.value.status_code == 401

