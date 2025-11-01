"""
Unit tests for Email Verification Service
Tests email verification functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from core.services.auth.email_verification_service import EmailVerificationService
from core.exceptions import (
    BusinessRuleException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)
from tests.factories import UserFactory


@pytest.fixture
def mock_repository():
    """Create mock user repository"""
    repo = Mock()
    repo.find_by_id = AsyncMock()
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
    settings.app_name = "Test Auth System"
    settings.app_url = "http://localhost:3000"
    settings.email_verification_expire_hours = 24
    settings.require_email_verification = True
    settings_provider.get_settings.return_value = settings
    return settings_provider


@pytest.fixture
def email_verification_service(mock_repository, mock_email_service, mock_settings):
    """Create email verification service instance"""
    return EmailVerificationService(mock_repository, mock_email_service, mock_settings)


@pytest.mark.unit
class TestSendVerificationEmail:
    """Test sending verification email"""
    
    @pytest.mark.asyncio
    async def test_send_verification_email_generates_token(
        self, email_verification_service, mock_repository, mock_email_service
    ):
        """Test sending verification email generates token"""
        user = UserFactory.create(email_verified=False)
        mock_repository.find_by_id.return_value = user
        mock_repository.save.return_value = user
        
        await email_verification_service.send_verification_email(user.id, user.client_id)
        
        assert user.email_verification_token is not None
        assert user.email_verification_sent_at is not None
        assert mock_repository.save.called
        assert mock_email_service.send_email.called
    
    @pytest.mark.asyncio
    async def test_send_verification_email_includes_link(
        self, email_verification_service, mock_repository, mock_email_service
    ):
        """Test verification email includes link"""
        user = UserFactory.create()
        mock_repository.find_by_id.return_value = user
        mock_repository.save.return_value = user
        
        await email_verification_service.send_verification_email(user.id, user.client_id)
        
        # Check email was sent
        assert mock_email_service.send_email.called
        call_args = mock_email_service.send_email.call_args
        email_html = call_args[1]['html_content']
        assert 'verify' in email_html.lower()
    
    @pytest.mark.asyncio
    async def test_send_verification_to_nonexistent_user_raises(
        self, email_verification_service, mock_repository
    ):
        """Test sending verification to nonexistent user raises exception"""
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(UserNotFoundException):
            await email_verification_service.send_verification_email("nonexistent", "client")
    
    @pytest.mark.asyncio
    async def test_send_verification_to_already_verified_user_raises(
        self, email_verification_service, mock_repository
    ):
        """Test sending verification to already verified user raises exception"""
        user = UserFactory.create(email_verified=True)
        mock_repository.find_by_id.return_value = user
        
        with pytest.raises(BusinessRuleException, match="already verified"):
            await email_verification_service.send_verification_email(user.id, user.client_id)


@pytest.mark.unit
class TestVerifyEmail:
    """Test email verification"""
    
    @pytest.mark.asyncio
    async def test_verify_email_with_valid_token(
        self, email_verification_service, mock_repository
    ):
        """Test verifying email with valid token"""
        user = UserFactory.create(email_verified=False)
        # Generate token
        user.generate_email_verification_token()
        token = user.email_verification_token
        
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        result = await email_verification_service.verify_email(user.email, token, user.client_id)
        
        assert result.email_verified is True
        assert result.email_verification_token is None
        assert mock_repository.save.called
    
    @pytest.mark.asyncio
    async def test_verify_email_with_invalid_token_raises(
        self, email_verification_service, mock_repository
    ):
        """Test verifying email with invalid token raises exception"""
        user = UserFactory.create(email_verified=False)
        user.generate_email_verification_token()
        
        mock_repository.find_by_email.return_value = user
        
        with pytest.raises(InvalidTokenException):
            await email_verification_service.verify_email(user.email, "wrong-token", user.client_id)
    
    @pytest.mark.asyncio
    async def test_verify_email_with_expired_token_raises(
        self, email_verification_service, mock_repository
    ):
        """Test verifying email with expired token raises exception"""
        user = UserFactory.create(email_verified=False)
        user.generate_email_verification_token()
        # Set sent_at to 25 hours ago (expired)
        user.email_verification_sent_at = datetime.utcnow() - timedelta(hours=25)
        
        token = user.email_verification_token
        mock_repository.find_by_email.return_value = user
        
        with pytest.raises(TokenExpiredException):
            await email_verification_service.verify_email(user.email, token, user.client_id)
    
    @pytest.mark.asyncio
    async def test_verify_email_for_nonexistent_user_raises(
        self, email_verification_service, mock_repository
    ):
        """Test verifying email for nonexistent user raises exception"""
        mock_repository.find_by_email.return_value = None
        
        with pytest.raises(UserNotFoundException):
            await email_verification_service.verify_email("nonexistent@test.com", "token", "client")


@pytest.mark.unit
class TestResendVerificationEmail:
    """Test resending verification email"""
    
    @pytest.mark.asyncio
    async def test_resend_verification_email(
        self, email_verification_service, mock_repository, mock_email_service
    ):
        """Test resending verification email"""
        user = UserFactory.create(email_verified=False)
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        await email_verification_service.resend_verification_email(user.email, user.client_id)
        
        assert user.email_verification_token is not None
        assert mock_email_service.send_email.called
    
    @pytest.mark.asyncio
    async def test_resend_to_verified_user_raises(
        self, email_verification_service, mock_repository
    ):
        """Test resending to already verified user raises exception"""
        user = UserFactory.create(email_verified=True)
        mock_repository.find_by_email.return_value = user
        
        with pytest.raises(BusinessRuleException, match="already verified"):
            await email_verification_service.resend_verification_email(user.email, user.client_id)
    
    @pytest.mark.asyncio
    async def test_resend_generates_new_token(
        self, email_verification_service, mock_repository, mock_email_service
    ):
        """Test resending generates new token"""
        user = UserFactory.create(email_verified=False)
        user.generate_email_verification_token()
        old_token = user.email_verification_token
        
        mock_repository.find_by_email.return_value = user
        mock_repository.save.return_value = user
        
        await email_verification_service.resend_verification_email(user.email, user.client_id)
        
        # Should have generated new token
        assert user.email_verification_token != old_token


@pytest.mark.unit
class TestEmailGeneration:
    """Test email HTML generation"""
    
    def test_generate_verification_email_html(self, email_verification_service):
        """Test generating verification email HTML"""
        html = email_verification_service._generate_verification_email_html(
            user_name="Test User",
            verification_link="http://localhost:3000/verify?token=abc123"
        )
        
        assert "Test User" in html
        assert "verify" in html.lower()
        assert "http://localhost:3000/verify?token=abc123" in html
    
    def test_email_includes_app_name(self, email_verification_service):
        """Test email includes app name"""
        html = email_verification_service._generate_verification_email_html(
            user_name="User",
            verification_link="http://test.com/verify"
        )
        
        assert "Test Auth System" in html
    
    def test_email_includes_expiration_info(self, email_verification_service):
        """Test email includes expiration info"""
        html = email_verification_service._generate_verification_email_html(
            user_name="User",
            verification_link="http://test.com/verify"
        )
        
        assert "24 hours" in html or "expire" in html.lower()


@pytest.mark.unit
class TestEmailVerificationStatus:
    """Test checking verification status"""
    
    @pytest.mark.asyncio
    async def test_check_verification_status_verified(
        self, email_verification_service, mock_repository
    ):
        """Test checking status for verified user"""
        user = UserFactory.create(email_verified=True)
        mock_repository.find_by_id.return_value = user
        
        status = await email_verification_service.get_verification_status(user.id, user.client_id)
        
        assert status["email_verified"] is True
        assert "email_verification_sent_at" in status
    
    @pytest.mark.asyncio
    async def test_check_verification_status_not_verified(
        self, email_verification_service, mock_repository
    ):
        """Test checking status for unverified user"""
        user = UserFactory.create(email_verified=False)
        mock_repository.find_by_id.return_value = user
        
        status = await email_verification_service.get_verification_status(user.id, user.client_id)
        
        assert status["email_verified"] is False

