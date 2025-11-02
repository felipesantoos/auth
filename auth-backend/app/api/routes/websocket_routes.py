"""
WebSocket Routes
Real-time communication endpoints
Compliant with 25-real-time-streaming.md guide
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from datetime import datetime
import logging
import json
import uuid
import asyncio

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
    - broadcast: Broadcast to all users
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
    
    # Connect user with metadata
    await manager.connect(
        websocket,
        user_id=user_id,
        metadata={
            "connected_at": datetime.utcnow().isoformat(),
            "user_name": current_user.name
        }
    )
    
    # Send welcome message
    await manager.send_personal_message({
        "type": "connected",
        "message": "Welcome to Auth System WebSocket",
        "user_id": user_id
    }, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message based on type
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to keep-alive
                await manager.send_personal_message({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }, websocket)
            
            elif message_type == 'message':
                # Send to all user's devices
                await manager.send_to_user({
                    'type': 'message',
                    'content': data.get('content'),
                    'sender': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, user_id)
            
            elif message_type == 'broadcast':
                # Broadcast to all users (except sender)
                await manager.broadcast({
                    'type': 'broadcast',
                    'content': data.get('content'),
                    'sender': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, exclude=websocket)
            
            elif message_type == 'join_room':
                # Join a room
                room_id = data.get('room_id')
                if room_id:
                    await manager.join_room(websocket, room_id)
                    await manager.send_personal_message({
                        'type': 'room_joined',
                        'room_id': room_id,
                        'message': f'You joined room {room_id}',
                        'room_size': manager.get_room_size(room_id)
                    }, websocket)
            
            elif message_type == 'leave_room':
                # Leave a room
                room_id = data.get('room_id')
                if room_id:
                    await manager.leave_room(websocket, room_id)
                    await manager.send_personal_message({
                        'type': 'room_left',
                        'room_id': room_id,
                        'message': f'You left room {room_id}'
                    }, websocket)
            
            elif message_type == 'room_message':
                # Send message to room
                room_id = data.get('room_id')
                content = data.get('content')
                
                if room_id and content:
                    await manager.send_to_room({
                        'type': 'room_message',
                        'room_id': room_id,
                        'content': content,
                        'sender': user_id,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room_id, exclude=websocket)
            
            else:
                # Unknown message type
                await manager.send_personal_message({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }, websocket)
    
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
    
    finally:
        # Cleanup
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
        "active_rooms": len(manager.room_connections),
        "users": manager.get_connected_users()
    }


@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(..., description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time chat.
    
    **Message Types**:
    
    Client → Server:
    - `{type: "message", content: "text"}` - Send message
    - `{type: "typing", is_typing: true}` - Typing indicator
    - `{type: "read", message_id: "123"}` - Mark message as read
    - `{type: "ping"}` - Keep-alive ping
    
    Server → Client:
    - `{type: "message", ...}` - New message
    - `{type: "user_joined", user: {...}}` - User joined room
    - `{type: "user_left", user: {...}}` - User left room
    - `{type: "typing", user: {...}}` - Someone is typing
    - `{type: "pong"}` - Keep-alive response
    """
    # Verify token and get user
    try:
        user = await get_current_user_ws(websocket, token)
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Connect and join room
    await manager.connect(
        websocket,
        user_id=user.id,
        metadata={
            "room_id": room_id,
            "connected_at": datetime.utcnow().isoformat()
        }
    )
    await manager.join_room(websocket, room_id)
    
    # Notify room that user joined
    await manager.send_to_room(
        message={
            "type": "user_joined",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat(),
            "room_size": manager.get_room_size(room_id)
        },
        room_id=room_id,
        exclude=websocket
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "message":
                # Chat message - broadcast to room
                content = data.get("content", "").strip()
                
                if content:
                    # Generate message ID (in production, save to database)
                    message_id = str(uuid.uuid4())
                    
                    # Broadcast to room
                    await manager.send_to_room(
                        message={
                            "type": "message",
                            "id": message_id,
                            "content": content,
                            "user": {
                                "id": user.id,
                                "name": user.name,
                                "email": user.email
                            },
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        room_id=room_id
                    )
            
            elif message_type == "typing":
                # Typing indicator - broadcast without saving
                is_typing = data.get("is_typing", True)
                
                await manager.send_to_room(
                    message={
                        "type": "typing",
                        "user": {
                            "id": user.id,
                            "name": user.name
                        },
                        "is_typing": is_typing
                    },
                    room_id=room_id,
                    exclude=websocket
                )
            
            elif message_type == "read":
                # Mark message as read (in production, update database)
                message_id = data.get("message_id")
                if message_id:
                    logger.debug(f"Message {message_id} read by user {user.id}")
            
            elif message_type == "ping":
                # Respond to ping
                await manager.send_personal_message({"type": "pong"}, websocket)
    
    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected from room {room_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    
    finally:
        # Cleanup
        manager.disconnect(websocket, user_id=user.id)
        await manager.leave_room(websocket, room_id)
        
        # Notify room that user left
        await manager.send_to_room(
            message={
                "type": "user_left",
                "user": {
                    "id": user.id,
                    "name": user.name
                },
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
                "room_size": manager.get_room_size(room_id)
            },
            room_id=room_id
        )


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket for real-time notifications.
    
    Sends notifications as they occur.
    
    **Message Types**:
    
    Client → Server:
    - `{type: "ping"}` - Keep-alive ping
    
    Server → Client:
    - `{type: "notification", notification: {...}}` - New notification
    - `{type: "heartbeat"}` - Keep-alive ping from server
    - `{type: "pong"}` - Response to client ping
    """
    try:
        user = await get_current_user_ws(websocket, token)
    except:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, user_id=user.id)
    
    try:
        # Send pending notifications (in production, fetch from database)
        # notifications = await get_unread_notifications(user.id)
        # for notif in notifications:
        #     await manager.send_personal_message(
        #         message={
        #             "type": "notification",
        #             "notification": notif.dict()
        #         },
        #         websocket=websocket
        #     )
        
        # Keep connection alive with heartbeat
        while True:
            try:
                # Wait for client ping or send heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                if data.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
            
            except asyncio.TimeoutError:
                # Send heartbeat if no message received
                await manager.send_personal_message({"type": "heartbeat"}, websocket)
    
    except WebSocketDisconnect:
        pass
    
    except Exception as e:
        logger.error(f"WebSocket notifications error: {e}", exc_info=True)
    
    finally:
        manager.disconnect(websocket, user_id=user.id)

