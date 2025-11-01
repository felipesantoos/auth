"""
WebSocket Connection Manager
Manages active WebSocket connections for real-time communication
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
    """
    
    def __init__(self):
        # Store connections by user_id (List allows multiple devices per user)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Store room memberships: room_id -> Set[user_id]
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        
        connection_count = sum(len(conns) for conns in self.active_connections.values())
        logger.info(
            f"WebSocket connected",
            extra={
                "user_id": user_id,
                "user_connection_count": len(self.active_connections[user_id]),
                "total_connections": connection_count
            }
        )
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Remove user from all rooms
                for room_id in list(self.rooms.keys()):
                    if user_id in self.rooms[room_id]:
                        self.rooms[room_id].remove(user_id)
                        
                        # Clean up empty rooms
                        if not self.rooms[room_id]:
                            del self.rooms[room_id]
        
        connection_count = sum(len(conns) for conns in self.active_connections.values())
        logger.info(
            f"WebSocket disconnected",
            extra={
                "user_id": user_id,
                "total_connections": connection_count
            }
        )
    
    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send message to specific user (all their connections/devices).
        
        Args:
            message: Message data (will be JSON encoded)
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up failed connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict, exclude_user: str = None):
        """
        Broadcast message to all connected users.
        
        Args:
            message: Message data (will be JSON encoded)
            exclude_user: Optional user ID to exclude from broadcast
        """
        sent_count = 0
        failed_count = 0
        
        for user_id, connections in list(self.active_connections.items()):
            if user_id != exclude_user:
                disconnected = []
                
                for connection in connections:
                    try:
                        await connection.send_json(message)
                        sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to broadcast to {user_id}: {e}")
                        disconnected.append(connection)
                        failed_count += 1
                
                # Clean up failed connections
                for conn in disconnected:
                    self.disconnect(conn, user_id)
        
        logger.debug(
            f"Broadcast sent",
            extra={
                "sent": sent_count,
                "failed": failed_count,
                "exclude_user": exclude_user
            }
        )
    
    async def join_room(self, user_id: str, room_id: str):
        """
        Add user to a room for room-based messaging.
        
        Args:
            user_id: User ID
            room_id: Room ID
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(user_id)
        
        logger.info(f"User {user_id} joined room {room_id}")
    
    async def leave_room(self, user_id: str, room_id: str):
        """
        Remove user from a room.
        
        Args:
            user_id: User ID
            room_id: Room ID
        """
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            self.rooms[room_id].remove(user_id)
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            
            logger.info(f"User {user_id} left room {room_id}")
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str = None):
        """
        Broadcast message to all users in a specific room.
        
        Args:
            room_id: Room ID
            message: Message data (will be JSON encoded)
            exclude_user: Optional user ID to exclude from broadcast
        """
        if room_id not in self.rooms:
            logger.warning(f"Attempted to broadcast to non-existent room: {room_id}")
            return
        
        sent_count = 0
        failed_count = 0
        
        for user_id in self.rooms[room_id]:
            if user_id != exclude_user:
                try:
                    await self.send_personal_message(message, user_id)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send room message to {user_id}: {e}")
                    failed_count += 1
        
        logger.debug(
            f"Room broadcast sent",
            extra={
                "room_id": room_id,
                "sent": sent_count,
                "failed": failed_count
            }
        )
    
    def get_connected_users(self) -> List[str]:
        """
        Get list of currently connected user IDs.
        
        Returns:
            List of user IDs with active connections
        """
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections.
        
        Returns:
            Total connection count
        """
        return sum(len(conns) for conns in self.active_connections.values())
    
    def is_user_connected(self, user_id: str) -> bool:
        """
        Check if a user has any active connections.
        
        Args:
            user_id: User ID to check
        
        Returns:
            True if user is connected, False otherwise
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Singleton instance
manager = ConnectionManager()

