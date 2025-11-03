"""
Test User Profile Service
"""
import pytest
from unittest.mock import Mock, AsyncMock
import bcrypt
from core.services.auth.user_profile_service import UserProfileService
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole


@pytest.fixture
def mock_user_repository():
    """Mock user repository"""
    repo = Mock()
    repo.find_by_id = AsyncMock()
    repo.find_by_username = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.save = AsyncMock()
    return repo


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
    settings.app_name = "Test App"
    settings.cors_origins_list = ["http://localhost:5173"]
    provider.get_settings = Mock(return_value=settings)
    return provider


@pytest.fixture
def test_user():
    """Create test user"""
    password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return AppUser(
        id="user-123",
        username="testuser",
        email="test@example.com",
        name="Test User",        _password_hash=password_hash,
        active=True
    )


class TestUserProfileService:
    """Test user profile service"""
    
    @pytest.mark.asyncio
    async def test_update_profile_name(
        self,
        mock_user_repository,
        mock_email_service,
        mock_settings_provider,
        test_user
    ):
        """Test updating profile name"""
        mock_user_repository.find_by_id.return_value = test_user
        mock_user_repository.save.return_value = test_user
        
        service = UserProfileService(
            mock_user_repository,
            mock_email_service,
            mock_settings_provider
        )
        
        updated = await service.update_profile(
            user_id="user-123",            name="New Name"
        )
        
        assert updated.name == "New Name"
        assert mock_user_repository.save.called
    
    @pytest.mark.asyncio
    async def test_update_profile_username_unique(
        self,
        mock_user_repository,
        mock_email_service,
        mock_settings_provider,
        test_user
    ):
        """Test updating username checks uniqueness"""
        mock_user_repository.find_by_id.return_value = test_user
        mock_user_repository.find_by_username.return_value = None  # Username available
        mock_user_repository.save.return_value = test_user
        
        service = UserProfileService(
            mock_user_repository,
            mock_email_service,
            mock_settings_provider
        )
        
        updated = await service.update_profile(
            user_id="user-123",            username="newusername"
        )
        
        assert updated.username == "newusername"
    
    @pytest.mark.asyncio
    async def test_update_profile_username_taken(
        self,
        mock_user_repository,
        mock_email_service,
        mock_settings_provider,
        test_user
    ):
        """Test updating to taken username fails"""
        mock_user_repository.find_by_id.return_value = test_user
        # Another user already has this username
        other_user = AppUser(id="other-123", username="taken", email="other@example.com",
                            name="Other", role=UserRole.USER,                            _password_hash="hash", active=True)
        mock_user_repository.find_by_username.return_value = other_user
        
        service = UserProfileService(
            mock_user_repository,
            mock_email_service,
            mock_settings_provider
        )
        
        with pytest.raises(ValueError, match="Username already taken"):
            await service.update_profile(
                user_id="user-123",                username="taken"
            )
    
    @pytest.mark.asyncio
    async def test_delete_account_with_correct_password(
        self,
        mock_user_repository,
        mock_email_service,
        mock_settings_provider,
        test_user
    ):
        """Test deleting account with correct password"""
        mock_user_repository.find_by_id.return_value = test_user
        mock_user_repository.save.return_value = test_user
        
        service = UserProfileService(
            mock_user_repository,
            mock_email_service,
            mock_settings_provider
        )
        
        result = await service.delete_account(
            user_id="user-123",
            password="password123"
        )
        
        assert result is True
        assert not test_user.active
        assert mock_user_repository.save.called
    
    @pytest.mark.asyncio
    async def test_delete_account_with_wrong_password(
        self,
        mock_user_repository,
        mock_email_service,
        mock_settings_provider,
        test_user
    ):
        """Test deleting account with wrong password fails"""
        mock_user_repository.find_by_id.return_value = test_user
        
        service = UserProfileService(
            mock_user_repository,
            mock_email_service,
            mock_settings_provider
        )
        
        with pytest.raises(ValueError, match="Incorrect password"):
            await service.delete_account(
                user_id="user-123",
                password="wrongpassword"
            )

