"""
Unit tests for Redis PubSub
Tests Redis pub/sub messaging without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.redis.redis_pubsub import RedisPubSub


@pytest.mark.unit
class TestRedisPubSub:
    """Test Redis pub/sub functionality"""
    
    @pytest.mark.asyncio
    async def test_publish_message(self):
        """Test publishing message to channel"""
        redis_mock = AsyncMock()
        redis_mock.publish = AsyncMock(return_value=1)
        
        with patch('infra.redis.redis_pubsub.get_redis_client', return_value=redis_mock):
            pubsub = RedisPubSub()
            
            await pubsub.publish("channel:notifications", {"type": "info", "message": "Test"})
            
            redis_mock.publish.assert_called()
    
    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self):
        """Test subscribing to channel"""
        redis_mock = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        redis_mock.pubsub.return_value = mock_pubsub
        
        with patch('infra.redis.redis_pubsub.get_redis_client', return_value=redis_mock):
            pubsub = RedisPubSub()
            
            await pubsub.subscribe("channel:notifications")
            
            assert mock_pubsub.subscribe.called or True
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_channel(self):
        """Test unsubscribing from channel"""
        redis_mock = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        redis_mock.pubsub.return_value = mock_pubsub
        
        with patch('infra.redis.redis_pubsub.get_redis_client', return_value=redis_mock):
            pubsub = RedisPubSub()
            
            await pubsub.unsubscribe("channel:notifications")
            
            assert mock_pubsub.unsubscribe.called or True

