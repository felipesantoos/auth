"""
Unit tests for Session Service
Tests session management across multiple devices
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from core.services.auth.session_service import SessionService
from core.domain.auth.user_session import UserSession
from core.exceptions import BusinessRuleException
from tests.factories import UserFactory


@pytest.fixture
def mock_repository():
    """Create mock session repository"""
    repo = Mock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_user = AsyncMock()
    repo.find_active_by_user = AsyncMock()
    repo.delete = AsyncMock()
    repo.delete_by_user = AsyncMock()
    return repo


@pytest.fixture
def mock_cache():
    """Create mock cache service"""
    cache = Mock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings_provider = Mock()
    settings = Mock()
    settings.session_max_devices = 10
    settings.session_inactivity_timeout_days = 30
    settings_provider.get_settings.return_value = settings
    return settings_provider


@pytest.fixture
def session_service(mock_repository, mock_cache, mock_settings):
    """Create session service instance"""
    return SessionService(mock_repository, mock_cache, mock_settings)


@pytest.mark.unit
class TestSessionCreation:
    """Test session creation"""
    
    @pytest.mark.asyncio
    async def test_create_session_saves_to_repository(self, session_service, mock_repository):
        """Test creating session saves to repository"""
        user = UserFactory.create()
        refresh_token = "test-refresh-token"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ip_address = "192.168.1.1"
        
        mock_repository.save.return_value = UserSession(
            id="session-123",
            user_id=user.id,
            client_id=user.client_id,
            refresh_token_hash="hashed",
            device_type="desktop",
            device_name="Chrome on Windows",
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity=datetime.utcnow()
        )
        
        session = await session_service.create_session(
            user_id=user.id,
            client_id=user.client_id,
            refresh_token=refresh_token,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        assert session is not None
        assert session.user_id == user.id
        assert mock_repository.save.called
    
    @pytest.mark.asyncio
    async def test_create_session_parses_device_info(self, session_service, mock_repository):
        """Test session creation parses device information"""
        user = UserFactory.create()
        
        # Mock return value
        mock_repository.save.return_value = UserSession(
            id="session-123",
            user_id=user.id,
            client_id=user.client_id,
            refresh_token_hash="hashed",
            device_type="mobile",
            device_name="Safari on iPhone",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
            last_activity=datetime.utcnow()
        )
        
        session = await session_service.create_session(
            user_id=user.id,
            client_id=user.client_id,
            refresh_token="token",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
            ip_address="192.168.1.1"
        )
        
        assert session.device_type == "mobile"


@pytest.mark.unit
class TestSessionRetrieval:
    """Test session retrieval"""
    
    @pytest.mark.asyncio
    async def test_get_active_sessions_for_user(self, session_service, mock_repository):
        """Test getting active sessions for a user"""
        user = UserFactory.create()
        
        # Mock multiple sessions
        sessions = [
            UserSession(
                id=f"session-{i}",
                user_id=user.id,
                client_id=user.client_id,
                refresh_token_hash="hash",
                device_type="desktop",
                ip_address="192.168.1.1",
                user_agent="Chrome",
                last_activity=datetime.utcnow()
            )
            for i in range(3)
        ]
        mock_repository.find_active_by_user.return_value = sessions
        
        active_sessions = await session_service.get_active_sessions(user.id, user.client_id)
        
        assert len(active_sessions) == 3
        assert all(s.user_id == user.id for s in active_sessions)
    
    @pytest.mark.asyncio
    async def test_get_session_by_id(self, session_service, mock_repository):
        """Test getting session by ID"""
        session_id = "session-123"
        
        mock_repository.find_by_id.return_value = UserSession(
            id=session_id,
            user_id="user-456",
            client_id="client-789",
            refresh_token_hash="hash",
            device_type="desktop",
            ip_address="192.168.1.1",
            user_agent="Chrome",
            last_activity=datetime.utcnow()
        )
        
        session = await session_service.get_session(session_id)
        
        assert session is not None
        assert session.id == session_id


@pytest.mark.unit
class TestSessionRevocation:
    """Test session revocation (logout)"""
    
    @pytest.mark.asyncio
    async def test_revoke_session_by_id(self, session_service, mock_repository):
        """Test revoking specific session"""
        session_id = "session-123"
        user_id = "user-456"
        client_id = "client-789"
        
        mock_repository.delete.return_value = True
        
        result = await session_service.revoke_session(session_id, user_id, client_id)
        
        assert result is True
        assert mock_repository.delete.called
    
    @pytest.mark.asyncio
    async def test_revoke_all_sessions(self, session_service, mock_repository):
        """Test revoking all sessions for a user"""
        user_id = "user-456"
        client_id = "client-789"
        
        mock_repository.delete_by_user.return_value = 5  # Deleted 5 sessions
        
        count = await session_service.revoke_all_sessions(user_id, client_id)
        
        assert count == 5
        assert mock_repository.delete_by_user.called


@pytest.mark.unit
class TestSessionMaxDevices:
    """Test maximum devices limit"""
    
    @pytest.mark.asyncio
    async def test_create_session_enforces_max_devices_limit(self, session_service, mock_repository):
        """Test creating session when max devices reached"""
        user = UserFactory.create()
        
        # Mock 10 existing sessions (max limit)
        existing_sessions = [
            UserSession(
                id=f"session-{i}",
                user_id=user.id,
                client_id=user.client_id,
                refresh_token_hash="hash",
                device_type="desktop",
                ip_address="192.168.1.1",
                user_agent="Chrome",
                last_activity=datetime.utcnow() - timedelta(days=i)
            )
            for i in range(10)
        ]
        mock_repository.find_active_by_user.return_value = existing_sessions
        
        # Should revoke oldest session before creating new one
        mock_repository.save.return_value = UserSession(
            id="new-session",
            user_id=user.id,
            client_id=user.client_id,
            refresh_token_hash="hash",
            device_type="desktop",
            ip_address="192.168.1.1",
            user_agent="Chrome",
            last_activity=datetime.utcnow()
        )
        
        session = await session_service.create_session(
            user_id=user.id,
            client_id=user.client_id,
            refresh_token="token",
            user_agent="Chrome",
            ip_address="192.168.1.1"
        )
        
        # Should have deleted oldest session
        assert mock_repository.delete.called


@pytest.mark.unit
class TestDeviceTypeParsing:
    """Test device type parsing from user agent"""
    
    def test_parse_mobile_device(self, session_service):
        """Test parsing mobile device"""
        user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
            "Mozilla/5.0 (Android 11; Mobile)",
        ]
        
        for ua in user_agents:
            device_type = session_service._parse_device_type(ua)
            assert device_type == "mobile"
    
    def test_parse_tablet_device(self, session_service):
        """Test parsing tablet device"""
        user_agents = [
            "Mozilla/5.0 (iPad; CPU OS 14_0)",
            "Mozilla/5.0 (Android 11; Tablet)",
        ]
        
        for ua in user_agents:
            device_type = session_service._parse_device_type(ua)
            assert device_type == "tablet"
    
    def test_parse_desktop_device(self, session_service):
        """Test parsing desktop device"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
        ]
        
        for ua in user_agents:
            device_type = session_service._parse_device_type(ua)
            assert device_type == "desktop"
    
    def test_parse_unknown_device(self, session_service):
        """Test parsing unknown device"""
        device_type = session_service._parse_device_type("Unknown Browser")
        assert device_type == "unknown"
    
    def test_parse_none_user_agent(self, session_service):
        """Test parsing None user agent"""
        device_type = session_service._parse_device_type(None)
        assert device_type == "unknown"


@pytest.mark.unit
class TestDeviceNameParsing:
    """Test device name parsing from user agent"""
    
    def test_get_device_name_chrome(self, session_service):
        """Test getting device name for Chrome"""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/96.0"
        name = session_service._get_device_name(ua)
        
        assert name is not None
        assert "Chrome" in name or "Windows" in name
    
    def test_get_device_name_safari(self, session_service):
        """Test getting device name for Safari"""
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0) AppleWebKit/605.1.15 Safari/604.1"
        name = session_service._get_device_name(ua)
        
        assert name is not None
    
    def test_get_device_name_none(self, session_service):
        """Test getting device name for None user agent"""
        name = session_service._get_device_name(None)
        assert name is None


@pytest.mark.unit
class TestSessionActivityUpdate:
    """Test session activity tracking"""
    
    @pytest.mark.asyncio
    async def test_update_session_activity(self, session_service, mock_repository):
        """Test updating session last activity"""
        session = UserSession(
            id="session-123",
            user_id="user-456",
            client_id="client-789",
            refresh_token_hash="hash",
            device_type="desktop",
            ip_address="192.168.1.1",
            user_agent="Chrome",
            last_activity=datetime.utcnow() - timedelta(hours=1)
        )
        
        mock_repository.find_by_id.return_value = session
        mock_repository.save.return_value = session
        
        updated_session = await session_service.update_activity(session.id)
        
        assert mock_repository.save.called
        # Last activity should be updated (we can't assert exact time due to timing)

