"""
Unit tests for ApiKeyScope domain model
Tests domain logic without external dependencies
"""
import pytest
from core.domain.auth.api_key_scope import ApiKeyScope


@pytest.mark.unit
class TestApiKeyScopePermissions:
    """Test scope permission checks"""
    
    def test_read_user_is_read_only(self):
        """Test READ_USER scope is read-only"""
        scope = ApiKeyScope.READ_USER
        assert scope.is_read_only() is True
        assert scope.is_write_scope() is False
    
    def test_read_resource_is_read_only(self):
        """Test READ_RESOURCE scope is read-only"""
        scope = ApiKeyScope.READ_RESOURCE
        assert scope.is_read_only() is True
        assert scope.is_write_scope() is False
    
    def test_read_session_is_read_only(self):
        """Test READ_SESSION scope is read-only"""
        scope = ApiKeyScope.READ_SESSION
        assert scope.is_read_only() is True
        assert scope.is_write_scope() is False
    
    def test_read_audit_is_read_only(self):
        """Test READ_AUDIT scope is read-only"""
        scope = ApiKeyScope.READ_AUDIT
        assert scope.is_read_only() is True
        assert scope.is_write_scope() is False
    
    def test_write_user_is_write_scope(self):
        """Test WRITE_USER scope is write scope"""
        scope = ApiKeyScope.WRITE_USER
        assert scope.is_read_only() is False
        assert scope.is_write_scope() is True
    
    def test_write_resource_is_write_scope(self):
        """Test WRITE_RESOURCE scope is write scope"""
        scope = ApiKeyScope.WRITE_RESOURCE
        assert scope.is_read_only() is False
        assert scope.is_write_scope() is True
    
    def test_delete_user_is_write_scope(self):
        """Test DELETE_USER scope is write scope"""
        scope = ApiKeyScope.DELETE_USER
        assert scope.is_read_only() is False
        assert scope.is_write_scope() is True
    
    def test_delete_resource_is_write_scope(self):
        """Test DELETE_RESOURCE scope is write scope"""
        scope = ApiKeyScope.DELETE_RESOURCE
        assert scope.is_read_only() is False
        assert scope.is_write_scope() is True
    
    def test_manage_session_is_write_scope(self):
        """Test MANAGE_SESSION scope is write scope"""
        scope = ApiKeyScope.MANAGE_SESSION
        assert scope.is_read_only() is False
        assert scope.is_write_scope() is True


@pytest.mark.unit
class TestApiKeyScopeAdmin:
    """Test admin scope checks"""
    
    def test_admin_scope_is_admin(self):
        """Test ADMIN scope is identified as admin"""
        scope = ApiKeyScope.ADMIN
        assert scope.is_admin_scope() is True
    
    def test_read_user_is_not_admin(self):
        """Test READ_USER scope is not admin"""
        scope = ApiKeyScope.READ_USER
        assert scope.is_admin_scope() is False
    
    def test_write_user_is_not_admin(self):
        """Test WRITE_USER scope is not admin"""
        scope = ApiKeyScope.WRITE_USER
        assert scope.is_admin_scope() is False
    
    def test_delete_user_is_not_admin(self):
        """Test DELETE_USER scope is not admin"""
        scope = ApiKeyScope.DELETE_USER
        assert scope.is_admin_scope() is False


@pytest.mark.unit
class TestApiKeyScopeValues:
    """Test enum values"""
    
    def test_read_user_value(self):
        """Test READ_USER has correct value"""
        assert ApiKeyScope.READ_USER.value == "read:user"
    
    def test_write_user_value(self):
        """Test WRITE_USER has correct value"""
        assert ApiKeyScope.WRITE_USER.value == "write:user"
    
    def test_delete_user_value(self):
        """Test DELETE_USER has correct value"""
        assert ApiKeyScope.DELETE_USER.value == "delete:user"
    
    def test_read_resource_value(self):
        """Test READ_RESOURCE has correct value"""
        assert ApiKeyScope.READ_RESOURCE.value == "read:resource"
    
    def test_write_resource_value(self):
        """Test WRITE_RESOURCE has correct value"""
        assert ApiKeyScope.WRITE_RESOURCE.value == "write:resource"
    
    def test_delete_resource_value(self):
        """Test DELETE_RESOURCE has correct value"""
        assert ApiKeyScope.DELETE_RESOURCE.value == "delete:resource"
    
    def test_read_session_value(self):
        """Test READ_SESSION has correct value"""
        assert ApiKeyScope.READ_SESSION.value == "read:session"
    
    def test_manage_session_value(self):
        """Test MANAGE_SESSION has correct value"""
        assert ApiKeyScope.MANAGE_SESSION.value == "manage:session"
    
    def test_admin_value(self):
        """Test ADMIN has correct value"""
        assert ApiKeyScope.ADMIN.value == "admin"
    
    def test_read_audit_value(self):
        """Test READ_AUDIT has correct value"""
        assert ApiKeyScope.READ_AUDIT.value == "read:audit"
    
    def test_all_scopes_have_string_values(self):
        """Test all scopes have string values"""
        for scope in ApiKeyScope:
            assert isinstance(scope.value, str)
            assert len(scope.value) > 0

