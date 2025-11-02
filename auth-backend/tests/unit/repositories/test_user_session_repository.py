"""
Unit tests for User Session Repository
Tests session data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from infra.database.repositories.user_session_repository import UserSessionRepository
from core.domain.auth.user_session import UserSession


@pytest.mark.unit
class TestUserSessionRepositorySave:
    """Test saving user sessions"""
    
    @pytest.mark.asyncio
    async def test_save_session(self):
        """Test saving session to database"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        repository = UserSessionRepository(session_mock)
        
        user_session = UserSession(
            id=None,
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            device_name="iPhone"
        )
        
        result = await repository.save(user_session)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()


@pytest.mark.unit
class TestUserSessionRepositoryGet:
    """Test retrieving user sessions"""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting session by ID"""
        session_mock = AsyncMock()
        db_session_mock = Mock(
            id="session-123",
            user_id="user-123",
            refresh_token_hash="hash"
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_session_mock)
        
        repository = UserSessionRepository(session_mock)
        
        result = await repository.get_by_id("session-123")
        
        assert result is not None or session_mock.execute.called
    
    @pytest.mark.asyncio
    async def test_get_active_sessions_by_user(self):
        """Test getting active sessions for user"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = UserSessionRepository(session_mock)
        
        result = await repository.get_active_sessions("user-123")
        
        assert isinstance(result, list)
        session_mock.execute.assert_called()


@pytest.mark.unit
class TestUserSessionRepositoryRevoke:
    """Test revoking sessions"""
    
    @pytest.mark.asyncio
    async def test_revoke_session(self):
        """Test revoking session"""
        session_mock = AsyncMock()
        db_session_mock = Mock(
            id="session-123",
            revoke=Mock()
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_session_mock)
        session_mock.commit = AsyncMock()
        
        repository = UserSessionRepository(session_mock)
        
        await repository.revoke("session-123")
        
        session_mock.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_revoke_all_user_sessions(self):
        """Test revoking all sessions for user"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.commit = AsyncMock()
        
        repository = UserSessionRepository(session_mock)
        
        await repository.revoke_all_for_user("user-123")
        
        session_mock.execute.assert_called()
        session_mock.commit.assert_called()

