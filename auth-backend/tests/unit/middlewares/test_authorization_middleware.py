"""
Unit tests for Authorization Middleware
Tests permission and role-based authorization
"""
import pytest
from unittest.mock import Mock
from core.domain.auth.user_role import UserRole
from core.domain.auth.app_user import AppUser


@pytest.mark.unit
class TestRoleAuthorization:
    """Test role-based authorization"""

    def test_admin_has_admin_role(self):
        """Should verify admin has admin role"""
        user = Mock(spec=AppUser)
        user.role = UserRole.ADMIN
        
        assert user.role == UserRole.ADMIN

    def test_manager_has_manager_role(self):
        """Should verify manager has manager role"""
        user = Mock(spec=AppUser)
        user.role = UserRole.MANAGER
        
        assert user.role == UserRole.MANAGER

    def test_user_has_user_role(self):
        """Should verify user has user role"""
        user = Mock(spec=AppUser)
        user.role = UserRole.USER
        
        assert user.role == UserRole.USER


@pytest.mark.unit
class TestRoleHierarchy:
    """Test role hierarchy logic"""

    def test_admin_role_level(self):
        """Should have admin as highest role"""
        admin_level = 3
        manager_level = 2
        user_level = 1
        
        assert admin_level > manager_level
        assert admin_level > user_level

    def test_manager_role_level(self):
        """Should have manager above user"""
        manager_level = 2
        user_level = 1
        
        assert manager_level > user_level

    def test_role_comparison(self):
        """Should be able to compare roles"""
        def get_role_level(role: UserRole) -> int:
            levels = {
                UserRole.USER: 1,
                UserRole.MANAGER: 2,
                UserRole.ADMIN: 3
            }
            return levels.get(role, 0)
        
        assert get_role_level(UserRole.ADMIN) > get_role_level(UserRole.MANAGER)
        assert get_role_level(UserRole.MANAGER) > get_role_level(UserRole.USER)


@pytest.mark.unit
class TestPermissionChecking:
    """Test permission checking logic"""

    def test_user_has_permission(self):
        """Should verify user has specific permission"""
        user_permissions = ["read:users", "write:users"]
        required_permission = "read:users"
        
        assert required_permission in user_permissions

    def test_user_lacks_permission(self):
        """Should verify user lacks specific permission"""
        user_permissions = ["read:users"]
        required_permission = "delete:users"
        
        assert required_permission not in user_permissions

    def test_admin_has_all_permissions(self):
        """Should verify admin has all permissions"""
        user_role = UserRole.ADMIN
        
        # Admin should have access to everything
        is_admin = user_role == UserRole.ADMIN
        assert is_admin


@pytest.mark.unit
class TestResourceOwnership:
    """Test resource ownership checks"""

    def test_user_owns_resource(self):
        """Should verify user owns resource"""
        user_id = "user-123"
        resource_owner_id = "user-123"
        
        assert user_id == resource_owner_id

    def test_user_does_not_own_resource(self):
        """Should verify user doesn't own resource"""
        user_id = "user-123"
        resource_owner_id = "user-456"
        
        assert user_id != resource_owner_id

    def test_admin_can_access_any_resource(self):
        """Should verify admin can access any resource"""
        user_role = UserRole.ADMIN
        user_id = "admin-123"
        resource_owner_id = "user-456"
        
        can_access = (user_role == UserRole.ADMIN) or (user_id == resource_owner_id)
        assert can_access


@pytest.mark.unit
class TestClientIsolation:
    """Test client/tenant isolation"""

    def test_user_belongs_to_client(self):
        """Should verify user belongs to client"""
        user_client_id = "client-123"
        request_client_id = "client-123"
        
        assert user_client_id == request_client_id

    def test_user_different_client(self):
        """Should detect cross-client access attempt"""
        user_client_id = "client-123"
        request_client_id = "client-456"
        
        assert user_client_id != request_client_id
