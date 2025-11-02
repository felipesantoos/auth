"""
Unit tests for UserRole domain model
Tests domain logic without external dependencies
"""
import pytest
from core.domain.auth.user_role import UserRole


@pytest.mark.unit
class TestUserRoleValues:
    """Test enum values"""
    
    def test_admin_role_value(self):
        """Test ADMIN role has correct value"""
        assert UserRole.ADMIN.value == "admin"
    
    def test_manager_role_value(self):
        """Test MANAGER role has correct value"""
        assert UserRole.MANAGER.value == "manager"
    
    def test_user_role_value(self):
        """Test USER role has correct value"""
        assert UserRole.USER.value == "user"
    
    def test_all_roles_have_string_values(self):
        """Test all roles have string values"""
        for role in UserRole:
            assert isinstance(role.value, str)
            assert len(role.value) > 0
    
    def test_role_values_are_unique(self):
        """Test all role values are unique"""
        values = [role.value for role in UserRole]
        assert len(values) == len(set(values))


@pytest.mark.unit
class TestUserRoleStringRepresentation:
    """Test string representation"""
    
    def test_admin_string_representation(self):
        """Test ADMIN role string representation"""
        role = UserRole.ADMIN
        assert str(role) == "admin"
    
    def test_manager_string_representation(self):
        """Test MANAGER role string representation"""
        role = UserRole.MANAGER
        assert str(role) == "manager"
    
    def test_user_string_representation(self):
        """Test USER role string representation"""
        role = UserRole.USER
        assert str(role) == "user"


@pytest.mark.unit
class TestUserRoleComparison:
    """Test role comparison"""
    
    def test_admin_equals_admin(self):
        """Test ADMIN equals ADMIN"""
        assert UserRole.ADMIN == UserRole.ADMIN
    
    def test_manager_equals_manager(self):
        """Test MANAGER equals MANAGER"""
        assert UserRole.MANAGER == UserRole.MANAGER
    
    def test_user_equals_user(self):
        """Test USER equals USER"""
        assert UserRole.USER == UserRole.USER
    
    def test_admin_not_equals_manager(self):
        """Test ADMIN not equals MANAGER"""
        assert UserRole.ADMIN != UserRole.MANAGER
    
    def test_admin_not_equals_user(self):
        """Test ADMIN not equals USER"""
        assert UserRole.ADMIN != UserRole.USER
    
    def test_manager_not_equals_user(self):
        """Test MANAGER not equals USER"""
        assert UserRole.MANAGER != UserRole.USER

