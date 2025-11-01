"""
Unit tests for Passwordless Service
Tests magic link authentication functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from core.services.auth.passwordless_service import PasswordlessService
from core.exceptions import (
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)
from tests.factories import UserFactory


@pytest.fixture
def mock_repository():
    """Create mock user repository"""
    repo = Mock()
    repo.find_by_email = AsyncMock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_email_service():
    """Create mock email service"""
    email = Mock()
    email.send_email = AsyncMock()
    return email


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings_provider = Mock()
    settings = Mock()
    settings.app_name = "Test Auth"
    settings.app_url = "http://localhost:3000"
    settings.magic_link_expire_minutes = 15
    settings_provider.get_settings.return_value = settings
    return settings_provider


@pytest.fixture
def passwordless_service(mock_repository, mock_email_service, mock_settings):
    """Create passwordless service instance"""
    return PasswordlessService(mock_repository, mock_email_service, mock_settings)


@pytest.mark.unit
class TestSendMagicLink:
    """Test sending magic link"""
    
    @pytest.mark.asyncio
    async def test_send_magic_link_generates_token(
        self, passwordless_service, mock_repository, mock_email_service
    ):
        """Test sending magic link generates token"""
        user = UserFactory.build()
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        await passwordless_service.send_magic_link(user.email, user.client_id)
        
        assert user.magic_link_token is not None
        assert user.magic_link_sent_at is not None
        assert mock_repository.save.called
        assert mock_email_service.send_email.called
    
    @pytest.mark.asyncio
    async def test_send_magic_link_to_nonexistent_user_raises(
        self, passwordless_service, mock_repository
    ):
        """Test sending magic link to nonexistent user raises exception"""
        mock_repository.find_by_email.return_value = None
        
        with pytest.raises(UserNotFoundException):
            await passwordless_service.send_magic_link("nonexistent@test.com", "client")
    
    @pytest.mark.asyncio
    async def test_send_magic_link_includes_link_in_email(
        self, passwordless_service, mock_repository, mock_email_service
    ):
        """Test magic link email includes link"""
        user = UserFactory.build()
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        await passwordless_service.send_magic_link(user.email, user.client_id)
        
        assert mock_email_service.send_email.called
        call_args = mock_email_service.send_email.call_args
        assert 'login' in call_args[1]['subject'].lower()


@pytest.mark.unit
class TestVerifyMagicLink:
    """Test verifying magic link"""
    
    @pytest.mark.asyncio
    async def test_verify_valid_magic_link(
        self, passwordless_service, mock_repository
    ):
        """Test verifying valid magic link"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        token = user.magic_link_token
        
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        result = await passwordless_service.verify_magic_link(user.email, token, user.client_id)
        
        assert result is not None
        assert result.id == user.id
        # Token should be cleared after use
        assert user.magic_link_token is None
        assert mock_repository.save.called
    
    @pytest.mark.asyncio
    async def test_verify_invalid_magic_link_raises(
        self, passwordless_service, mock_repository
    ):
        """Test verifying invalid magic link raises exception"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        
        mock_repository.find_by_email.return_value = user
        
        with pytest.raises(InvalidTokenException):
            await passwordless_service.verify_magic_link(user.email, "wrong-token", user.client_id)
    
    @pytest.mark.asyncio
    async def test_verify_expired_magic_link_raises(
        self, passwordless_service, mock_repository
    ):
        """Test verifying expired magic link raises exception"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        # Set sent_at to 20 minutes ago (expired)
        user.magic_link_sent_at = datetime.utcnow() - timedelta(minutes=20)
        
        token = user.magic_link_token
        mock_repository.find_by_email.return_value = user
        
        with pytest.raises(TokenExpiredException):
            await passwordless_service.verify_magic_link(user.email, token, user.client_id)
    
    @pytest.mark.asyncio
    async def test_verify_magic_link_for_nonexistent_user_raises(
        self, passwordless_service, mock_repository
    ):
        """Test verifying magic link for nonexistent user raises exception"""
        mock_repository.find_by_email.return_value = None
        
        with pytest.raises(UserNotFoundException):
            await passwordless_service.verify_magic_link("nonexistent@test.com", "token", "client")


@pytest.mark.unit
class TestMagicLinkEmailGeneration:
    """Test magic link email generation"""
    
    def test_generate_magic_link_email_html(self, passwordless_service):
        """Test generating magic link email HTML"""
        html = passwordless_service._generate_magic_link_email_html(
            user_name="Test User",
            magic_link="http://localhost:3000/login?token=abc123"
        )
        
        assert "Test User" in html
        assert "login" in html.lower() or "sign in" in html.lower()
        assert "http://localhost:3000/login?token=abc123" in html
    
    def test_magic_link_email_includes_expiration(self, passwordless_service):
        """Test magic link email includes expiration info"""
        html = passwordless_service._generate_magic_link_email_html(
            user_name="User",
            magic_link="http://test.com/login"
        )
        
        assert "15 minutes" in html or "expire" in html.lower()


@pytest.mark.unit
class TestMagicLinkSecurity:
    """Test magic link security features"""
    
    @pytest.mark.asyncio
    async def test_magic_link_one_time_use(
        self, passwordless_service, mock_repository
    ):
        """Test magic link can only be used once"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        token = user.magic_link_token
        
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        # First use
        await passwordless_service.verify_magic_link(user.email, token, user.client_id)
        
        # Token should be cleared
        assert user.magic_link_token is None
        
        # Second use should fail
        with pytest.raises(InvalidTokenException):
            await passwordless_service.verify_magic_link(user.email, token, user.client_id)
    
    @pytest.mark.asyncio
    async def test_sending_new_magic_link_invalidates_old(
        self, passwordless_service, mock_repository, mock_email_service
    ):
        """Test sending new magic link invalidates old one"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        old_token = user.magic_link_token
        
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        # Send new magic link
        await passwordless_service.send_magic_link(user.email, user.client_id)
        
        # Should have new token
        assert user.magic_link_token != old_token

