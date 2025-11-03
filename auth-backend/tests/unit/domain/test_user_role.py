"""
Unit tests for UserRole enum
Tests role enumeration and string representation
"""
import pytest
from core.domain.auth.user_role import UserRole


@pytest.mark.unit
class TestUserRoleValues:
    """Test UserRole enum values"""

    def test_admin_role_value(self):
        """Admin role should have correct value"""
        assert UserRole.ADMIN.value == "admin"

    def test_manager_role_value(self):
        """Manager role should have correct value"""
        assert UserRole.MANAGER.value == "manager"

    def test_user_role_value(self):
        """User role should have correct value"""
        assert UserRole.USER.value == "user"

    def test_all_roles_have_string_values(self):
        """All roles should have string values"""
        for role in UserRole:
            assert isinstance(role.value, str)

    def test_role_values_are_unique(self):
        """All role values should be unique"""
        values = [role.value for role in UserRole]
        assert len(values) == len(set(values))


@pytest.mark.unit
class TestUserRoleStringRepresentation:
    """Test UserRole string representation"""

    def test_admin_string_representation(self):
        """Admin role string representation"""
        assert str(UserRole.ADMIN) == "admin"

    def test_manager_string_representation(self):
        """Manager role string representation"""
        assert str(UserRole.MANAGER) == "manager"

    def test_user_string_representation(self):
        """User role string representation"""
        assert str(UserRole.USER) == "user"


@pytest.mark.unit
class TestUserRoleComparison:
    """Test UserRole comparison"""

    def test_admin_equals_admin(self):
        """Admin role should equal admin role"""
        assert UserRole.ADMIN == UserRole.ADMIN

    def test_manager_equals_manager(self):
        """Manager role should equal manager role"""
        assert UserRole.MANAGER == UserRole.MANAGER

    def test_user_equals_user(self):
        """User role should equal user role"""
        assert UserRole.USER == UserRole.USER

    def test_admin_not_equals_manager(self):
        """Admin role should not equal manager role"""
        assert UserRole.ADMIN != UserRole.MANAGER

    def test_admin_not_equals_user(self):
        """Admin role should not equal user role"""
        assert UserRole.ADMIN != UserRole.USER

    def test_manager_not_equals_user(self):
        """Manager role should not equal user role"""
        assert UserRole.MANAGER != UserRole.USER

