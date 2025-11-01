"""
Unit tests for AuthMapper
Tests conversion between domain models and DTOs
"""
import pytest
from datetime import datetime
from app.api.mappers.auth_mapper import AuthMapper
from app.api.dtos.response.auth_response import UserResponse, TokenResponse
from core.domain.auth.user_role import UserRole
from tests.factories import UserFactory


@pytest.mark.unit
class TestAuthMapperToUserResponse:
    """Test converting AppUser domain to UserResponse DTO"""
    
    def test_to_user_response_maps_all_fields(self):
        """Test to_user_response maps all fields correctly"""
        user = UserFactory.create(
            id="user-123",
            username="testuser",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            active=True,
            client_id="client-456",
            created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        response = AuthMapper.to_user_response(user)
        
        assert isinstance(response, UserResponse)
        assert response.id == "user-123"
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.name == "Test User"
        assert response.role == "user"  # Enum converted to value
        assert response.active is True
        assert response.client_id == "client-456"
        assert response.created_at == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_to_user_response_converts_role_enum_to_string(self):
        """Test role enum is converted to string value"""
        admin_user = UserFactory.create_admin()
        manager_user = UserFactory.create_manager()
        regular_user = UserFactory.create(role=UserRole.USER)
        
        admin_response = AuthMapper.to_user_response(admin_user)
        manager_response = AuthMapper.to_user_response(manager_user)
        user_response = AuthMapper.to_user_response(regular_user)
        
        assert admin_response.role == "admin"
        assert manager_response.role == "manager"
        assert user_response.role == "user"
    
    def test_to_user_response_preserves_active_status(self):
        """Test active status is preserved"""
        active_user = UserFactory.create(active=True)
        inactive_user = UserFactory.create(active=False)
        
        active_response = AuthMapper.to_user_response(active_user)
        inactive_response = AuthMapper.to_user_response(inactive_user)
        
        assert active_response.active is True
        assert inactive_response.active is False
    
    def test_to_user_response_includes_client_id(self):
        """Test client_id is included (multi-tenant)"""
        user = UserFactory.create(client_id="client-abc")
        
        response = AuthMapper.to_user_response(user)
        
        assert response.client_id == "client-abc"


@pytest.mark.unit
class TestAuthMapperToTokenResponse:
    """Test converting tokens and user to TokenResponse DTO"""
    
    def test_to_token_response_includes_all_fields(self):
        """Test to_token_response includes all required fields"""
        user = UserFactory.create()
        access_token = "access_token_value"
        refresh_token = "refresh_token_value"
        
        response = AuthMapper.to_token_response(access_token, refresh_token, user)
        
        assert isinstance(response, TokenResponse)
        assert response.access_token == "access_token_value"
        assert response.refresh_token == "refresh_token_value"
        assert response.token_type == "bearer"
        assert response.expires_in > 0  # Should be positive
        assert isinstance(response.user, UserResponse)
    
    def test_to_token_response_sets_token_type_to_bearer(self):
        """Test token_type is always 'bearer'"""
        user = UserFactory.create()
        
        response = AuthMapper.to_token_response("access", "refresh", user)
        
        assert response.token_type == "bearer"
    
    def test_to_token_response_includes_user_data(self):
        """Test user data is included in response"""
        user = UserFactory.create(
            id="user-123",
            username="testuser",
            email="test@example.com"
        )
        
        response = AuthMapper.to_token_response("access", "refresh", user)
        
        assert response.user.id == "user-123"
        assert response.user.username == "testuser"
        assert response.user.email == "test@example.com"
    
    def test_to_token_response_calculates_expires_in_seconds(self):
        """Test expires_in is in seconds"""
        user = UserFactory.create()
        
        response = AuthMapper.to_token_response("access", "refresh", user)
        
        # expires_in should be in seconds (minutes * 60)
        # Default is typically 30 minutes = 1800 seconds
        assert response.expires_in >= 60  # At least 1 minute
        assert isinstance(response.expires_in, int)


@pytest.mark.unit
class TestAuthMapperNullHandling:
    """Test mapper handles null/None values correctly"""
    
    def test_to_user_response_handles_none_created_at(self):
        """Test mapper handles None created_at"""
        user = UserFactory.create(created_at=None)
        
        response = AuthMapper.to_user_response(user)
        
        assert response.created_at is None
    
    def test_to_user_response_handles_none_id(self):
        """Test mapper handles None id (before persistence)"""
        user = UserFactory.create(id=None)
        
        response = AuthMapper.to_user_response(user)
        
        assert response.id is None


@pytest.mark.unit
class TestAuthMapperConsistency:
    """Test mapper produces consistent results"""
    
    def test_same_user_produces_same_response(self):
        """Test mapping same user twice produces same result"""
        user = UserFactory.create()
        
        response1 = AuthMapper.to_user_response(user)
        response2 = AuthMapper.to_user_response(user)
        
        assert response1.id == response2.id
        assert response1.username == response2.username
        assert response1.email == response2.email
        assert response1.role == response2.role
    
    def test_different_users_produce_different_responses(self):
        """Test mapping different users produces different results"""
        user1 = UserFactory.create(username="user1", email="user1@example.com")
        user2 = UserFactory.create(username="user2", email="user2@example.com")
        
        response1 = AuthMapper.to_user_response(user1)
        response2 = AuthMapper.to_user_response(user2)
        
        assert response1.username != response2.username
        assert response1.email != response2.email

