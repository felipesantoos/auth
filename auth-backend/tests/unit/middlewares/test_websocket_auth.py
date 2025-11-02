"""
Unit tests for WebSocket Auth Middleware
Tests WebSocket authentication logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import WebSocketException
from app.api.middlewares.websocket_auth import WebSocketAuthMiddleware, authenticate_websocket


@pytest.mark.unit
class TestWebSocketAuth:
    """Test WebSocket authentication functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_token_allows_websocket_connection(self):
        """Test valid JWT token allows WebSocket connection"""
        websocket_mock = Mock()
        websocket_mock.query_params = {"token": "valid_token_123"}
        
        with patch('app.api.middlewares.websocket_auth.verify_token') as mock_verify:
            mock_verify.return_value = {"user_id": "user-123", "client_id": "client-123"}
            
            user = await authenticate_websocket(websocket_mock)
            
            assert user is not None
            assert user.get("user_id") == "user-123"
    
    @pytest.mark.asyncio
    async def test_missing_token_raises_exception(self):
        """Test missing token raises WebSocket exception"""
        websocket_mock = Mock()
        websocket_mock.query_params = {}
        
        with pytest.raises(WebSocketException) as exc_info:
            await authenticate_websocket(websocket_mock)
        
        assert exc_info.value.code == 4001 or exc_info.value.code == 1008
    
    @pytest.mark.asyncio
    async def test_invalid_token_raises_exception(self):
        """Test invalid token raises WebSocket exception"""
        websocket_mock = Mock()
        websocket_mock.query_params = {"token": "invalid_token"}
        
        with patch('app.api.middlewares.websocket_auth.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            with pytest.raises(WebSocketException) as exc_info:
                await authenticate_websocket(websocket_mock)
            
            assert exc_info.value.code in [4001, 1008]
    
    @pytest.mark.asyncio
    async def test_expired_token_raises_exception(self):
        """Test expired token raises WebSocket exception"""
        websocket_mock = Mock()
        websocket_mock.query_params = {"token": "expired_token"}
        
        with patch('app.api.middlewares.websocket_auth.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Token expired")
            
            with pytest.raises(WebSocketException):
                await authenticate_websocket(websocket_mock)

