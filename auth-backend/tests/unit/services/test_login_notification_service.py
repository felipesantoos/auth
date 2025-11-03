"""
Test login notification service
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from core.services.auth.login_notification_service import LoginNotificationService
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_session import UserSession
from core.domain.auth.user_role import UserRole


@pytest.fixture
def mock_email_service():
    """Mock email service"""
    service = Mock()
    service.send_email = AsyncMock()
    return service


@pytest.fixture
def mock_settings_provider():
    """Mock settings provider"""
    provider = Mock()
    settings = Mock()
    settings.app_name = "Auth System Test"
    settings.cors_origins_list = ["http://localhost:5173"]
    provider.get_settings = Mock(return_value=settings)
    return provider


@pytest.fixture
def test_user():
    """Create test user"""
    return AppUser(
        id="user-123",
        username="testuser",
        email="test@example.com",
        name="Test User",        _password_hash="hashed",
        active=True
    )


@pytest.fixture
def test_session():
    """Create test session"""
    return UserSession(
        id="session-123",
        user_id="user-123",        refresh_token_hash="hashed",
        device_name="Chrome on Windows",
        device_type="desktop",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        location="São Paulo, Brazil",
        created_at=datetime.utcnow()
    )


class TestLoginNotificationService:
    """Test login notification service"""
    
    @pytest.mark.asyncio
    async def test_send_login_notification(
        self,
        mock_email_service,
        mock_settings_provider,
        test_user,
        test_session
    ):
        """Test sending login notification"""
        service = LoginNotificationService(mock_email_service, mock_settings_provider)
        
        await service.send_new_login_notification(test_user, test_session)
        
        # Email should be sent
        assert mock_email_service.send_email.called
        call_kwargs = mock_email_service.send_email.call_args[1]
        
        assert call_kwargs['to_email'] == 'test@example.com'
        assert 'New login' in call_kwargs['subject']
        assert 'Chrome on Windows' in call_kwargs['html_content']
        assert '192.168.1.100' in call_kwargs['html_content']
        assert 'São Paulo, Brazil' in call_kwargs['html_content']
    
    @pytest.mark.asyncio
    async def test_send_notification_handles_email_failure(
        self,
        mock_email_service,
        mock_settings_provider,
        test_user,
        test_session
    ):
        """Test notification doesn't raise exception if email fails"""
        mock_email_service.send_email.side_effect = Exception("Email service down")
        
        service = LoginNotificationService(mock_email_service, mock_settings_provider)
        
        # Should not raise exception
        await service.send_new_login_notification(test_user, test_session)
        
        assert mock_email_service.send_email.called
    
    def test_generate_email_html(
        self,
        mock_email_service,
        mock_settings_provider
    ):
        """Test HTML email generation"""
        service = LoginNotificationService(mock_email_service, mock_settings_provider)
        
        html = service._generate_email_html(
            user_name="John Doe",
            device_name="iPhone 14",
            device_type="mobile",
            ip_address="192.168.1.100",
            location="New York, USA",
            time="2025-01-15 10:30 UTC"
        )
        
        assert "John Doe" in html
        assert "iPhone 14" in html
        assert "mobile" in html
        assert "192.168.1.100" in html
        assert "New York, USA" in html
        assert "2025-01-15 10:30 UTC" in html
        assert "New Login Detected" in html
        assert "If this wasn't you" in html
        assert "Change your password" in html

