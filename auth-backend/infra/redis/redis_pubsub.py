"""
Redis Pub/Sub System
Real-time event broadcasting using Redis Pub/Sub
"""
import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisPubSub:
    """
    Redis Pub/Sub wrapper for event broadcasting.
    
    Supports:
    - Channel subscriptions
    - Event handlers with decorators
    - JSON message encoding/decoding
    - Automatic reconnection
    """
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis Pub/Sub.
        
        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.handlers: Dict[str, list] = {}
        self.subscribed_channels: set = set()
        self._listening = False
        self._listen_task: Optional[asyncio.Task] = None
    
    async def connect(self):
        """Connect to Redis."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            logger.info("Redis Pub/Sub connected")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        self._listening = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Redis Pub/Sub disconnected")
    
    async def subscribe(self, *channels: str):
        """
        Subscribe to one or more channels.
        
        Args:
            *channels: Channel names to subscribe to
        
        Example:
            >>> await pubsub.subscribe("notifications", "events")
        """
        if not self.pubsub:
            await self.connect()
        
        await self.pubsub.subscribe(*channels)
        self.subscribed_channels.update(channels)
        logger.info(f"Subscribed to channels: {', '.join(channels)}")
    
    async def unsubscribe(self, *channels: str):
        """
        Unsubscribe from channels.
        
        Args:
            *channels: Channel names to unsubscribe from
        """
        if self.pubsub:
            await self.pubsub.unsubscribe(*channels)
            self.subscribed_channels.difference_update(channels)
            logger.info(f"Unsubscribed from channels: {', '.join(channels)}")
    
    def on_message(self, channel: str):
        """
        Decorator to register a message handler for a channel.
        
        Args:
            channel: Channel name to handle messages from
        
        Example:
            >>> @pubsub.on_message("notifications")
            >>> async def handle_notification(data: dict):
            ...     print(f"Notification: {data}")
        """
        def decorator(func: Callable):
            if channel not in self.handlers:
                self.handlers[channel] = []
            self.handlers[channel].append(func)
            logger.debug(f"Registered handler for channel '{channel}': {func.__name__}")
            return func
        return decorator
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message data (will be JSON-encoded)
        
        Example:
            >>> await pubsub.publish("notifications", {
            ...     "user_id": "user_123",
            ...     "notification": {"title": "Hello", "body": "World"}
            ... })
        """
        if not self.redis_client:
            await self.connect()
        
        # Encode message as JSON
        json_message = json.dumps(message)
        
        # Publish to channel
        await self.redis_client.publish(channel, json_message)
        logger.debug(f"Published to '{channel}': {json_message[:100]}...")
    
    async def listen(self):
        """
        Start listening for messages on subscribed channels.
        
        This is a long-running coroutine that should be run as a background task.
        
        Example:
            >>> asyncio.create_task(pubsub.listen())
        """
        if not self.pubsub:
            await self.connect()
        
        self._listening = True
        logger.info("Started listening for Redis Pub/Sub messages")
        
        try:
            async for message in self.pubsub.listen():
                if not self._listening:
                    break
                
                # Skip non-message events (subscribe, unsubscribe, etc.)
                if message["type"] != "message":
                    continue
                
                channel = message["channel"]
                data_str = message["data"]
                
                # Decode JSON message
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in message from '{channel}': {data_str}")
                    continue
                
                # Call registered handlers
                if channel in self.handlers:
                    for handler in self.handlers[channel]:
                        try:
                            await handler(data)
                        except Exception as e:
                            logger.error(
                                f"Error in handler {handler.__name__} for channel '{channel}': {e}",
                                exc_info=True
                            )
                else:
                    logger.warning(f"No handlers registered for channel '{channel}'")
        
        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub listener cancelled")
        except Exception as e:
            logger.error(f"Error in Redis Pub/Sub listener: {e}", exc_info=True)
        finally:
            self._listening = False
    
    def is_listening(self) -> bool:
        """Check if currently listening for messages."""
        return self._listening
    
    def get_subscribed_channels(self) -> set:
        """Get set of currently subscribed channels."""
        return self.subscribed_channels.copy()


# Global Pub/Sub instance
_pubsub: Optional[RedisPubSub] = None


async def init_pubsub(redis_url: str) -> RedisPubSub:
    """
    Initialize global Redis Pub/Sub instance.
    
    Args:
        redis_url: Redis connection URL
    
    Returns:
        RedisPubSub instance
    
    Example:
        >>> pubsub = await init_pubsub("redis://localhost:6379/0")
        >>> await pubsub.subscribe("notifications")
        >>> asyncio.create_task(pubsub.listen())
    """
    global _pubsub
    
    if _pubsub is not None:
        logger.warning("Redis Pub/Sub already initialized")
        return _pubsub
    
    _pubsub = RedisPubSub(redis_url)
    await _pubsub.connect()
    
    logger.info("Global Redis Pub/Sub initialized")
    return _pubsub


async def close_pubsub():
    """Close global Redis Pub/Sub instance."""
    global _pubsub
    
    if _pubsub is not None:
        await _pubsub.disconnect()
        _pubsub = None
        logger.info("Global Redis Pub/Sub closed")


def get_pubsub() -> Optional[RedisPubSub]:
    """
    Get global Redis Pub/Sub instance.
    
    Returns:
        RedisPubSub instance or None if not initialized
    
    Example:
        >>> pubsub = get_pubsub()
        >>> if pubsub:
        ...     await pubsub.publish("events", {"type": "test"})
    """
    return _pubsub
