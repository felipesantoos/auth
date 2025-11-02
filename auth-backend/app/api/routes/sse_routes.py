"""
Server-Sent Events (SSE) Routes
Real-time event streaming using SSE for one-way server-to-client communication
"""
import asyncio
import json
import logging
from typing import Optional, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query
from sse_starlette.sse import EventSourceResponse
from app.api.middlewares.auth_middleware import get_current_user
from core.domain.auth.app_user import AppUser
from infra.redis.redis_pubsub import get_pubsub

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sse", tags=["Server-Sent Events"])


async def event_generator(
    user_id: str,
    channel: str,
    heartbeat_interval: int = 30
) -> AsyncGenerator[dict, None]:
    """
    Generate SSE events for a user.
    
    Args:
        user_id: User ID to filter events for
        channel: Redis Pub/Sub channel to listen to
        heartbeat_interval: Interval in seconds to send heartbeat (keep-alive)
    
    Yields:
        Event dictionaries with 'event', 'data', and optional 'id'
    """
    pubsub = get_pubsub()
    
    if not pubsub:
        logger.error("Redis Pub/Sub not initialized")
        yield {
            "event": "error",
            "data": json.dumps({"message": "Server configuration error"})
        }
        return
    
    # Queue to receive messages from Pub/Sub
    message_queue = asyncio.Queue()
    
    # Handler to receive messages
    async def handle_message(data: dict):
        """Filter and queue messages for this user."""
        # Filter by user_id if present
        if "user_id" in data:
            if data["user_id"] == user_id or data.get("broadcast", False):
                await message_queue.put(data)
        else:
            # Broadcast to all
            await message_queue.put(data)
    
    # Register handler
    if channel not in pubsub.handlers:
        pubsub.handlers[channel] = []
    pubsub.handlers[channel].append(handle_message)
    
    try:
        last_heartbeat = asyncio.get_event_loop().time()
        
        while True:
            try:
                # Wait for message with timeout (for heartbeat)
                message = await asyncio.wait_for(
                    message_queue.get(),
                    timeout=heartbeat_interval
                )
                
                # Send message event
                yield {
                    "event": "message",
                    "data": json.dumps(message),
                    "id": message.get("id", str(datetime.utcnow().timestamp()))
                }
                
                last_heartbeat = asyncio.get_event_loop().time()
            
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }
                    last_heartbeat = current_time
    
    except asyncio.CancelledError:
        logger.info(f"SSE connection cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Error in SSE event generator: {e}", exc_info=True)
        yield {
            "event": "error",
            "data": json.dumps({"message": "Internal server error"})
        }
    finally:
        # Cleanup: remove handler
        if channel in pubsub.handlers:
            try:
                pubsub.handlers[channel].remove(handle_message)
            except ValueError:
                pass


@router.get("/notifications")
async def sse_notifications(
    request: Request,
    current_user: AppUser = Depends(get_current_user),
):
    """
    SSE endpoint for real-time notifications.
    
    **Connection**:
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/notifications', {
        headers: {
            'Authorization': 'Bearer YOUR_TOKEN'
        }
    });
    
    eventSource.addEventListener('message', (event) => {
        const notification = JSON.parse(event.data);
        console.log('Notification:', notification);
    });
    
    eventSource.addEventListener('heartbeat', (event) => {
        console.log('Keep-alive ping');
    });
    
    eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
    };
    ```
    
    **Events**:
    - `message` - New notification
    - `heartbeat` - Keep-alive ping every 30 seconds
    - `error` - Error occurred
    
    **Authentication**:
    Requires valid JWT token in Authorization header.
    
    **Note**: SSE connections are one-way (server → client).
    For bi-directional communication, use WebSocket.
    """
    logger.info(f"SSE notifications connection established for user {current_user.id}")
    
    return EventSourceResponse(
        event_generator(
            user_id=current_user.id,
            channel="notifications",
            heartbeat_interval=30
        )
    )


@router.get("/events")
async def sse_events(
    request: Request,
    channel: str = Query("system_events", description="Event channel to subscribe to"),
    current_user: AppUser = Depends(get_current_user),
):
    """
    SSE endpoint for real-time system events.
    
    **Available Channels**:
    - `system_events` - System-wide events
    - `notifications` - User notifications
    - `cache_invalidation` - Cache invalidation events (admin only)
    
    **Connection**:
    ```javascript
    const eventSource = new EventSource(
        '/api/v1/sse/events?channel=system_events',
        {
            headers: {
                'Authorization': 'Bearer YOUR_TOKEN'
            }
        }
    );
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data);
    };
    ```
    
    **Authentication**:
    Requires valid JWT token.
    """
    # Validate channel access
    allowed_channels = ["system_events", "notifications"]
    
    # Admin-only channels
    if channel == "cache_invalidation":
        if current_user.role.value != "admin":
            # Send error and close
            async def error_generator():
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Unauthorized channel access"})
                }
            return EventSourceResponse(error_generator())
        allowed_channels.append("cache_invalidation")
    
    if channel not in allowed_channels:
        async def error_generator():
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Invalid channel: {channel}"})
            }
        return EventSourceResponse(error_generator())
    
    logger.info(f"SSE connection for user {current_user.id} on channel '{channel}'")
    
    return EventSourceResponse(
        event_generator(
            user_id=current_user.id,
            channel=channel,
            heartbeat_interval=30
        )
    )


@router.get("/live-feed")
async def sse_live_feed(
    request: Request,
    current_user: AppUser = Depends(get_current_user),
):
    """
    SSE endpoint for live activity feed.
    
    Streams real-time updates about:
    - New users
    - Login events
    - System changes
    - Audit events (admin only)
    
    **Connection**:
    ```javascript
    const eventSource = new EventSource('/api/v1/sse/live-feed');
    
    eventSource.addEventListener('user_registered', (event) => {
        console.log('New user:', JSON.parse(event.data));
    });
    
    eventSource.addEventListener('user_login', (event) => {
        console.log('User logged in:', JSON.parse(event.data));
    });
    ```
    """
    async def live_feed_generator() -> AsyncGenerator[dict, None]:
        """Generate live feed events."""
        pubsub = get_pubsub()
        
        if not pubsub:
            yield {
                "event": "error",
                "data": json.dumps({"message": "Service unavailable"})
            }
            return
        
        # Queue for feed events
        feed_queue = asyncio.Queue()
        
        # Subscribe to multiple channels
        channels = ["system_events", "notifications"]
        
        async def handle_feed_message(data: dict):
            """Handle messages from multiple channels."""
            await feed_queue.put(data)
        
        # Register handlers for all channels
        for channel in channels:
            if channel not in pubsub.handlers:
                pubsub.handlers[channel] = []
            pubsub.handlers[channel].append(handle_feed_message)
        
        try:
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(feed_queue.get(), timeout=30)
                    
                    # Determine event type
                    event_type = message.get("type", "message")
                    
                    yield {
                        "event": event_type,
                        "data": json.dumps(message),
                        "id": str(datetime.utcnow().timestamp())
                    }
                
                except asyncio.TimeoutError:
                    # Heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
                    }
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in live feed: {e}", exc_info=True)
        finally:
            # Cleanup
            for channel in channels:
                if channel in pubsub.handlers:
                    try:
                        pubsub.handlers[channel].remove(handle_feed_message)
                    except ValueError:
                        pass
    
    logger.info(f"SSE live feed connection for user {current_user.id}")
    
    return EventSourceResponse(live_feed_generator())
