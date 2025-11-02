"""
WebSocket Connection Manager
Manages active WebSocket connections for real-time communication
Compliant with 25-real-time-streaming.md guide
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manage WebSocket connections.
    
    Features:
    - Per-user connection tracking (supports multiple devices)
    - Personal messaging
    - Broadcasting to all users
    - Room-based broadcasting
    - Connection metadata storage
    - WebSocket-level room management
    """
    
    def __init__(self):
        # All active connections
        self.active_connections: List[WebSocket] = []
        
        # Connections grouped by user (supports multiple devices per user)
        self.user_connections: Dict[str, List[WebSocket]] = {}
        
        # Connections grouped by room/channel (stores WebSocket objects)
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        
        # Connection metadata (device info, IP, connection time, etc.)
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str = None,
        metadata: dict = None
    ):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier (optional)
            metadata: Additional connection metadata (device, IP, etc.)
        """
        await websocket.accept()
        
        # Register connection
        self.active_connections.append(websocket)
        
        # Track by user
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        
        # Store metadata
        if metadata:
            self.connection_metadata[websocket] = metadata
        
        logger.info(
            f"WebSocket connected",
            extra={
                "user_id": user_id,
                "total_connections": len(self.active_connections)
            }
        )
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID (optional, for faster cleanup)
        """
        # Remove from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            # Clean up empty user entry
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from all rooms
        for room_id, connections in list(self.room_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.room_connections[room_id]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(
            f"WebSocket disconnected",
            extra={
                "user_id": user_id,
                "total_connections": len(self.active_connections)
            }
        )
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to specific WebSocket connection.
        
        Args:
            message: Message data (will be JSON encoded)
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)
    
    async def send_to_user(self, message: dict, user_id: str):
        """
        Send message to all connections of a specific user (multi-device).
        
        Args:
            message: Message data (will be JSON encoded)
            user_id: Target user ID
        """
        if user_id in self.user_connections:
            dead_connections = []
            
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict, exclude: WebSocket = None):
        """
        Broadcast message to all active connections.
        
        Args:
            message: Message data (will be JSON encoded)
            exclude: Optional WebSocket connection to exclude from broadcast
        """
        dead_connections = []
        
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)
    
    async def join_room(self, websocket: WebSocket, room_id: str):
        """
        Add connection to a room.
        
        Args:
            websocket: WebSocket connection
            room_id: Room ID
        """
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(websocket)
        
        logger.info(
            f"Connection joined room",
            extra={
                "room_id": room_id,
                "room_size": len(self.room_connections[room_id])
            }
        )
    
    async def leave_room(self, websocket: WebSocket, room_id: str):
        """
        Remove connection from a room.
        
        Args:
            websocket: WebSocket connection
            room_id: Room ID
        """
        if room_id in self.room_connections:
            if websocket in self.room_connections[room_id]:
                self.room_connections[room_id].remove(websocket)
            
            # Clean up empty room
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
                logger.info(f"Room closed", extra={"room_id": room_id})
    
    async def send_to_room(
        self,
        message: dict,
        room_id: str,
        exclude: WebSocket = None
    ):
        """
        Send message to all connections in a room.
        
        Args:
            message: Message data (will be JSON encoded)
            room_id: Room ID
            exclude: Optional WebSocket connection to exclude from broadcast
        """
        if room_id not in self.room_connections:
            return
        
        dead_connections = []
        
        for connection in self.room_connections[room_id]:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            await self.leave_room(conn, room_id)
            self.disconnect(conn)
    
    def get_room_size(self, room_id: str) -> int:
        """
        Get number of connections in a room.
        
        Args:
            room_id: Room ID
        
        Returns:
            Number of connections in the room
        """
        return len(self.room_connections.get(room_id, set()))
    
    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of active connections for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of active connections for the user
        """
        return len(self.user_connections.get(user_id, []))
    
    def get_connected_users(self) -> List[str]:
        """
        Get list of currently connected user IDs.
        
        Returns:
            List of user IDs with active connections
        """
        return list(self.user_connections.keys())
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            Total connection count
        """
        return len(self.active_connections)
    
    def is_user_connected(self, user_id: str) -> bool:
        """
        Check if a user has any active connections.
        
        Args:
            user_id: User ID to check
        
        Returns:
            True if user is connected, False otherwise
        """
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0


# Singleton instance
manager = ConnectionManager()

