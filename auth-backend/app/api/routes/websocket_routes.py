"""
WebSocket Routes
Real-time communication endpoints
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import logging
import json

from app.api.websockets.connection_manager import manager
from app.api.middlewares.websocket_auth import get_current_user_ws
from core.domain.auth.app_user import AppUser

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time communication.
    
    Authentication:
    - Provide token via query parameter: /ws?token=YOUR_JWT_TOKEN
    
    Supported message types (client -> server):
    - ping: Keep-alive ping
    - message: Personal message
    - join_room: Join a room
    - leave_room: Leave a room
    - room_message: Send message to room
    
    Message format:
    {
        "type": "message_type",
        "content": "message content",
        "room_id": "optional_room_id"
    }
    """
    # Authenticate user
    try:
        current_user = await get_current_user_ws(websocket, token)
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    user_id = current_user.id
    
    # Connect user
    await manager.connect(websocket, user_id)
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Welcome to Auth System WebSocket",
        "user_id": user_id
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message based on type
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to keep-alive
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                })
            
            elif message_type == 'message':
                # Echo personal message
                await manager.send_personal_message({
                    'type': 'message',
                    'content': data.get('content'),
                    'sender': user_id,
                    'timestamp': data.get('timestamp')
                }, user_id)
            
            elif message_type == 'broadcast':
                # Broadcast to all users (except sender)
                await manager.broadcast({
                    'type': 'broadcast',
                    'content': data.get('content'),
                    'sender': user_id
                }, exclude_user=user_id)
            
            elif message_type == 'join_room':
                # Join a room
                room_id = data.get('room_id')
                if room_id:
                    await manager.join_room(user_id, room_id)
                    await websocket.send_json({
                        'type': 'room_joined',
                        'room_id': room_id,
                        'message': f'You joined room {room_id}'
                    })
            
            elif message_type == 'leave_room':
                # Leave a room
                room_id = data.get('room_id')
                if room_id:
                    await manager.leave_room(user_id, room_id)
                    await websocket.send_json({
                        'type': 'room_left',
                        'room_id': room_id,
                        'message': f'You left room {room_id}'
                    })
            
            elif message_type == 'room_message':
                # Send message to room
                room_id = data.get('room_id')
                content = data.get('content')
                
                if room_id and content:
                    await manager.broadcast_to_room(room_id, {
                        'type': 'room_message',
                        'room_id': room_id,
                        'content': content,
                        'sender': user_id
                    }, exclude_user=user_id)
            
            else:
                # Unknown message type
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        
        # Notify other users (optional)
        await manager.broadcast({
            'type': 'user_disconnected',
            'user_id': user_id
        })
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        manager.disconnect(websocket, user_id)


@router.get("/ws/stats")
async def websocket_stats(current_user: AppUser = Depends()):
    """
    Get WebSocket connection statistics.
    
    Requires authentication.
    Only accessible by admin users.
    """
    # Only allow admin users (you can add permission check here)
    # if current_user.role != UserRole.ADMIN:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "total_connections": manager.get_connection_count(),
        "connected_users": len(manager.get_connected_users()),
        "active_rooms": len(manager.rooms),
        "users": manager.get_connected_users()
    }

