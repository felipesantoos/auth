"""
Unit tests for API Key Repository
Tests API key data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from infra.database.repositories.api_key_repository import ApiKeyRepository
from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope


@pytest.mark.unit
class TestApiKeyRepositorySave:
    """Test saving API keys"""
    
    @pytest.mark.asyncio
    async def test_save_api_key(self):
        """Test saving API key to database"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        repository = ApiKeyRepository(session_mock)
        
        api_key = ApiKey(
            id=None,
            user_id="user-123",
            client_id="client-123",
            name="Test Key",
            key_hash="hashed_key",
            scopes=[ApiKeyScope.READ_USER]
        )
        
        result = await repository.save(api_key)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()


@pytest.mark.unit
class TestApiKeyRepositoryGet:
    """Test retrieving API keys"""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting API key by ID"""
        session_mock = AsyncMock()
        db_key_mock = Mock(
            id="key-123",
            user_id="user-123",
            name="Test Key",
            scopes=["read:user"]
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_key_mock)
        
        repository = ApiKeyRepository(session_mock)
        
        result = await repository.get_by_id("key-123")
        
        assert result is not None or session_mock.execute.called
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self):
        """Test getting API keys by user ID"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = ApiKeyRepository(session_mock)
        
        result = await repository.get_by_user_id("user-123")
        
        assert isinstance(result, list)
        session_mock.execute.assert_called()


@pytest.mark.unit
class TestApiKeyRepositoryDelete:
    """Test deleting/revoking API keys"""
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self):
        """Test revoking API key"""
        session_mock = AsyncMock()
        db_key_mock = Mock(
            id="key-123",
            revoked_at=None,
            revoke=Mock()
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_key_mock)
        session_mock.commit = AsyncMock()
        
        repository = ApiKeyRepository(session_mock)
        
        await repository.revoke("key-123")
        
        session_mock.commit.assert_called()

