"""
Unit tests for Password Reset Service
Tests password reset functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import jwt
from datetime import datetime, timedelta
from core.services.auth.password_reset_service import PasswordResetService
from core.exceptions import (
    InvalidTokenException,
    UserNotFoundException,
    ValidationException,
)
from tests.factories import UserFactory


@pytest.fixture
def mock_repository():
    """Create mock user repository"""
    repo = Mock()
    repo.find_by_email = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.save = AsyncMock()
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
    settings.get_jwt_secret = Mock(return_value="test-secret-key-min-32-characters-long")
    settings.get_jwt_algorithm = Mock(return_value="HS256")
    settings.get_jwt_issuer = Mock(return_value="test-issuer")
    settings.get_jwt_audience = Mock(return_value="test-audience")
    settings_provider.get_settings.return_value = settings
    return settings_provider


@pytest.fixture
def password_reset_service(mock_repository, mock_cache, mock_settings, mock_email_service):
    """Create password reset service instance"""
    return PasswordResetService(mock_repository, mock_cache, mock_settings, mock_email_service)


@pytest.mark.unit
class TestRequestPasswordReset:
    """Test requesting password reset"""
    
    @pytest.mark.asyncio
    async def test_request_reset_generates_token(
        self, password_reset_service, mock_repository, mock_cache, mock_email_service
    ):
        """Test requesting reset generates token"""
        user = UserFactory.create()
        mock_repository.find_by_email.return_value = user
        
        await password_reset_service.request_password_reset(user.email, user.client_id)
        
        assert mock_cache.set.called
        assert mock_email_service.send_email.called
    
    @pytest.mark.asyncio
    async def test_request_reset_for_nonexistent_user_silent_fail(
        self, password_reset_service, mock_repository, mock_email_service
    ):
        """Test requesting reset for nonexistent user fails silently (security)"""
        mock_repository.find_by_email.return_value = None
        
        # Should not raise exception (prevent user enumeration)
        await password_reset_service.request_password_reset("nonexistent@test.com", "client")
        
        # Should not send email
        assert not mock_email_service.send_email.called
    
    @pytest.mark.asyncio
    async def test_request_reset_sends_email_with_link(
        self, password_reset_service, mock_repository, mock_email_service
    ):
        """Test reset request sends email with reset link"""
        user = UserFactory.create()
        mock_repository.find_by_email.return_value = user
        
        await password_reset_service.request_password_reset(user.email, user.client_id)
        
        assert mock_email_service.send_email.called
        call_args = mock_email_service.send_email.call_args
        assert call_args[1]['to'] == user.email
        assert 'reset' in call_args[1]['subject'].lower()


@pytest.mark.unit
class TestVerifyResetToken:
    """Test verifying reset token"""
    
    @pytest.mark.asyncio
    async def test_verify_valid_reset_token(
        self, password_reset_service, mock_cache
    ):
        """Test verifying valid reset token"""
        user = UserFactory.create()
        
        # Generate valid token
        token = password_reset_service._generate_reset_token(user.id, user.email, user.client_id)
        
        # Mock cache to return token exists
        mock_cache.get.return_value = "exists"
        
        result = await password_reset_service.verify_reset_token(token, user.client_id)
        
        assert result["user_id"] == user.id
        assert result["email"] == user.email
    
    @pytest.mark.asyncio
    async def test_verify_expired_reset_token_raises(
        self, password_reset_service, mock_cache
    ):
        """Test verifying expired token raises exception"""
        user = UserFactory.create()
        
        # Generate expired token
        with patch('core.services.auth.password_reset_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(hours=2)
            expired_token = password_reset_service._generate_reset_token(
                user.id, user.email, user.client_id
            )
        
        mock_cache.get.return_value = "exists"
        
        with pytest.raises(InvalidTokenException):
            await password_reset_service.verify_reset_token(expired_token, user.client_id)
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token_raises(
        self, password_reset_service
    ):
        """Test verifying invalid token raises exception"""
        with pytest.raises(InvalidTokenException):
            await password_reset_service.verify_reset_token("invalid-token", "client")
    
    @pytest.mark.asyncio
    async def test_verify_token_not_in_cache_raises(
        self, password_reset_service, mock_cache
    ):
        """Test verifying token not in cache raises exception"""
        user = UserFactory.create()
        token = password_reset_service._generate_reset_token(user.id, user.email, user.client_id)
        
        # Token not in cache (already used or never existed)
        mock_cache.get.return_value = None
        
        with pytest.raises(InvalidTokenException, match="used or invalid"):
            await password_reset_service.verify_reset_token(token, user.client_id)


@pytest.mark.unit
class TestResetPassword:
    """Test resetting password"""
    
    @pytest.mark.asyncio
    async def test_reset_password_with_valid_token(
        self, password_reset_service, mock_repository, mock_cache
    ):
        """Test resetting password with valid token"""
        user = UserFactory.create()
        token = password_reset_service._generate_reset_token(user.id, user.email, user.client_id)
        new_password = "NewSecurePass123"
        
        mock_cache.get.return_value = "exists"
        mock_repository.find_by_id.return_value = user
        mock_repository.save.return_value = user
        
        result = await password_reset_service.reset_password(token, new_password, user.client_id)
        
        assert result is not None
        assert mock_repository.save.called
        # Token should be deleted from cache (one-time use)
        assert mock_cache.delete.called
    
    @pytest.mark.asyncio
    async def test_reset_password_with_weak_password_raises(
        self, password_reset_service, mock_cache
    ):
        """Test resetting with weak password raises exception"""
        user = UserFactory.create()
        token = password_reset_service._generate_reset_token(user.id, user.email, user.client_id)
        
        mock_cache.get.return_value = "exists"
        
        with pytest.raises(ValidationException):
            await password_reset_service.reset_password(token, "weak", user.client_id)
    
    @pytest.mark.asyncio
    async def test_reset_password_invalidates_token(
        self, password_reset_service, mock_repository, mock_cache
    ):
        """Test reset password invalidates token (one-time use)"""
        user = UserFactory.create()
        token = password_reset_service._generate_reset_token(user.id, user.email, user.client_id)
        
        mock_cache.get.return_value = "exists"
        mock_repository.find_by_id.return_value = user
        mock_repository.save.return_value = user
        
        await password_reset_service.reset_password(token, "NewPass123", user.client_id)
        
        # Token should be deleted
        assert mock_cache.delete.called
        delete_call_args = mock_cache.delete.call_args
        assert token in str(delete_call_args)


@pytest.mark.unit
class TestTokenGeneration:
    """Test reset token generation"""
    
    def test_generate_reset_token(self, password_reset_service):
        """Test generating reset token"""
        user_id = "user-123"
        email = "test@example.com"
        client_id = "client-456"
        
        token = password_reset_service._generate_reset_token(user_id, email, client_id)
        
        assert token is not None
        assert len(token) > 20
        
        # Decode and verify
        settings = password_reset_service.settings
        decoded = jwt.decode(
            token,
            settings.get_jwt_secret(),
            algorithms=[settings.get_jwt_algorithm()],
            audience=settings.get_jwt_audience(),
            issuer=settings.get_jwt_issuer()
        )
        
        assert decoded["user_id"] == user_id
        assert decoded["email"] == email
        assert decoded["type"] == "password_reset"
    
    def test_generate_reset_token_includes_expiration(self, password_reset_service):
        """Test reset token includes expiration"""
        token = password_reset_service._generate_reset_token("user-123", "test@test.com", "client")
        
        settings = password_reset_service.settings
        decoded = jwt.decode(
            token,
            settings.get_jwt_secret(),
            algorithms=[settings.get_jwt_algorithm()],
            audience=settings.get_jwt_audience(),
            issuer=settings.get_jwt_issuer()
        )
        
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_tokens_are_unique(self, password_reset_service):
        """Test generated tokens are unique"""
        token1 = password_reset_service._generate_reset_token("user-123", "test@test.com", "client")
        token2 = password_reset_service._generate_reset_token("user-123", "test@test.com", "client")
        
        # Tokens should be different (different iat timestamps)
        assert token1 != token2


@pytest.mark.unit
class TestEmailGeneration:
    """Test reset email generation"""
    
    def test_generate_reset_email_html(self, password_reset_service):
        """Test generating reset email HTML"""
        html = password_reset_service._generate_reset_email_html(
            user_name="Test User",
            reset_link="http://localhost:3000/reset?token=abc123"
        )
        
        assert "Test User" in html
        assert "reset" in html.lower()
        assert "http://localhost:3000/reset?token=abc123" in html
    
    def test_reset_email_includes_app_name(self, password_reset_service):
        """Test reset email includes app name"""
        html = password_reset_service._generate_reset_email_html(
            user_name="User",
            reset_link="http://test.com/reset"
        )
        
        assert "Test Auth" in html
    
    def test_reset_email_includes_expiration_warning(self, password_reset_service):
        """Test reset email includes expiration warning"""
        html = password_reset_service._generate_reset_email_html(
            user_name="User",
            reset_link="http://test.com/reset"
        )
        
        assert "1 hour" in html or "expire" in html.lower()


@pytest.mark.unit
class TestCacheIntegration:
    """Test cache integration for token storage"""
    
    @pytest.mark.asyncio
    async def test_store_reset_token_in_cache(
        self, password_reset_service, mock_cache
    ):
        """Test storing reset token in cache"""
        token = "test-token"
        user_id = "user-123"
        client_id = "client-456"
        
        await password_reset_service._store_reset_token(token, user_id, client_id)
        
        assert mock_cache.set.called
        call_args = mock_cache.set.call_args
        # Should store with 1 hour TTL
        assert call_args[1]['ttl'] == 3600  # 1 hour in seconds
    
    @pytest.mark.asyncio
    async def test_check_token_exists_in_cache(
        self, password_reset_service, mock_cache
    ):
        """Test checking if token exists in cache"""
        token = "test-token"
        mock_cache.get.return_value = "user-123"
        
        result = await password_reset_service._check_token_exists(token)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_token_not_in_cache(
        self, password_reset_service, mock_cache
    ):
        """Test checking token not in cache"""
        token = "test-token"
        mock_cache.get.return_value = None
        
        result = await password_reset_service._check_token_exists(token)
        
        assert result is False

