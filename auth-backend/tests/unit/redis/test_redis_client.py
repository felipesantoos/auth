"""
Unit tests for Redis Client
Tests Redis client initialization and connection
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.redis.redis_client import RedisClient, get_redis_client


@pytest.mark.unit
class TestRedisClient:
    """Test Redis client functionality"""
    
    @pytest.mark.asyncio
    async def test_connect_to_redis(self):
        """Test connecting to Redis"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.return_value = AsyncMock()
            
            client = RedisClient(redis_url="redis://localhost:6379")
            await client.connect()
            
            assert mock_redis.called
    
    @pytest.mark.asyncio
    async def test_ping_redis(self):
        """Test pinging Redis to check connection"""
        with patch('redis.asyncio.from_url') as mock_redis:
            redis_instance = AsyncMock()
            redis_instance.ping = AsyncMock(return_value=True)
            mock_redis.return_value = redis_instance
            
            client = RedisClient(redis_url="redis://localhost:6379")
            await client.connect()
            
            is_alive = await client.ping()
            
            assert is_alive is True or redis_instance.ping.called
    
    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing Redis connection"""
        with patch('redis.asyncio.from_url') as mock_redis:
            redis_instance = AsyncMock()
            redis_instance.close = AsyncMock()
            mock_redis.return_value = redis_instance
            
            client = RedisClient(redis_url="redis://localhost:6379")
            await client.connect()
            await client.close()
            
            redis_instance.close.assert_called()

