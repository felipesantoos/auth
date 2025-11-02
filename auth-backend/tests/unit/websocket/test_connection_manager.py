"""
Unit tests for WebSocket Connection Manager
Tests WebSocket connection management logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from app.api.websockets.connection_manager import ConnectionManager


@pytest.mark.unit
class TestConnectionManager:
    """Test WebSocket connection manager functionality"""
    
    @pytest.mark.asyncio
    async def test_connect_adds_connection(self):
        """Test connecting adds WebSocket to active connections"""
        manager = ConnectionManager()
        websocket_mock = AsyncMock()
        
        await manager.connect(websocket_mock, user_id="user-123")
        
        assert "user-123" in manager.active_connections
        assert websocket_mock in manager.active_connections["user-123"]
    
    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        """Test disconnecting removes WebSocket from active connections"""
        manager = ConnectionManager()
        websocket_mock = AsyncMock()
        
        await manager.connect(websocket_mock, user_id="user-123")
        await manager.disconnect(websocket_mock, user_id="user-123")
        
        # Connection should be removed
        assert websocket_mock not in manager.active_connections.get("user-123", [])
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific user"""
        manager = ConnectionManager()
        websocket_mock = AsyncMock()
        websocket_mock.send_json = AsyncMock()
        
        await manager.connect(websocket_mock, user_id="user-123")
        await manager.send_personal_message(
            {"type": "notification", "data": "Hello"},
            user_id="user-123"
        )
        
        websocket_mock.send_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_users(self):
        """Test broadcast sends message to all connected users"""
        manager = ConnectionManager()
        
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()
        
        await manager.connect(ws1, user_id="user-1")
        await manager.connect(ws2, user_id="user-2")
        
        message = {"type": "announcement", "data": "System maintenance"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_get_user_connections(self):
        """Test getting all connections for a user"""
        manager = ConnectionManager()
        
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        
        await manager.connect(ws1, user_id="user-123")
        await manager.connect(ws2, user_id="user-123")  # Same user, different device
        
        connections = manager.get_user_connections("user-123")
        
        assert len(connections) == 2
        assert ws1 in connections
        assert ws2 in connections
    
    @pytest.mark.asyncio
    async def test_is_user_online(self):
        """Test checking if user is online"""
        manager = ConnectionManager()
        websocket_mock = AsyncMock()
        
        # User not online
        assert manager.is_user_online("user-123") is False
        
        # User connects
        await manager.connect(websocket_mock, user_id="user-123")
        assert manager.is_user_online("user-123") is True
        
        # User disconnects
        await manager.disconnect(websocket_mock, user_id="user-123")
        assert manager.is_user_online("user-123") is False
    
    @pytest.mark.asyncio
    async def test_get_online_users_count(self):
        """Test getting count of online users"""
        manager = ConnectionManager()
        
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()
        
        await manager.connect(ws1, user_id="user-1")
        await manager.connect(ws2, user_id="user-2")
        await manager.connect(ws3, user_id="user-2")  # Same user, different device
        
        online_count = manager.get_online_users_count()
        
        assert online_count == 2  # 2 unique users

