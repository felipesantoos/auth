"""
Unit tests for Permission domain model
Tests permission logic and resource access control
"""
import pytest
from datetime import datetime
from core.domain.auth.permission import Permission, PermissionAction
from tests.factories import PermissionFactory


@pytest.mark.unit
class TestPermissionAllows:
    """Test Permission.allows() method for access control"""
    
    def test_allows_returns_true_for_matching_action(self):
        """Test allows returns True when action matches"""
        permission = PermissionFactory.create(
            resource_type="project",
            resource_id="project-123",
            action=PermissionAction.READ
        )
        
        result = permission.allows(PermissionAction.READ, "project-123")
        assert result is True
    
    def test_allows_returns_false_for_different_action(self):
        """Test allows returns False when action doesn't match"""
        permission = PermissionFactory.create(
            resource_type="project",
            resource_id="project-123",
            action=PermissionAction.READ
        )
        
        result = permission.allows(PermissionAction.DELETE, "project-123")
        assert result is False
    
    def test_allows_returns_false_for_different_resource_id(self):
        """Test allows returns False when resource_id doesn't match"""
        permission = PermissionFactory.create(
            resource_type="project",
            resource_id="project-123",
            action=PermissionAction.READ
        )
        
        result = permission.allows(PermissionAction.READ, "project-456")
        assert result is False
    
    def test_allows_returns_true_for_wildcard_permission(self):
        """Test allows returns True for wildcard permission (no resource_id)"""
        permission = PermissionFactory.create_wildcard_permission(
            user_id="user-123",
            resource_type="project",
            action=PermissionAction.READ
        )
        
        # Should allow access to any project
        assert permission.allows(PermissionAction.READ, "project-123") is True
        assert permission.allows(PermissionAction.READ, "project-456") is True
        assert permission.allows(PermissionAction.READ, "project-789") is True
    
    def test_allows_returns_false_for_wildcard_with_wrong_action(self):
        """Test wildcard permission still checks action"""
        permission = PermissionFactory.create_wildcard_permission(
            user_id="user-123",
            resource_type="project",
            action=PermissionAction.READ
        )
        
        # Should not allow DELETE even though it's wildcard
        assert permission.allows(PermissionAction.DELETE, "project-123") is False


@pytest.mark.unit
class TestPermissionManageScope:
    """Test MANAGE permission scope (grants all actions)"""
    
    def test_manage_permission_allows_all_actions(self):
        """Test MANAGE permission allows all actions"""
        permission = PermissionFactory.create_manage_permission(
            user_id="user-123",
            resource_type="project",
            resource_id="project-123"
        )
        
        # MANAGE should allow all actions
        assert permission.allows(PermissionAction.READ, "project-123") is True
        assert permission.allows(PermissionAction.CREATE, "project-123") is True
        assert permission.allows(PermissionAction.UPDATE, "project-123") is True
        assert permission.allows(PermissionAction.DELETE, "project-123") is True
        assert permission.allows(PermissionAction.MANAGE, "project-123") is True
    
    def test_manage_permission_with_wildcard_allows_all_resources(self):
        """Test MANAGE wildcard permission allows all actions on all resources"""
        permission = PermissionFactory.create_manage_permission(
            user_id="user-123",
            resource_type="project",
            resource_id=None  # Wildcard
        )
        
        # Should allow all actions on any resource
        assert permission.allows(PermissionAction.READ, "project-123") is True
        assert permission.allows(PermissionAction.DELETE, "project-456") is True
        assert permission.allows(PermissionAction.UPDATE, "project-789") is True


@pytest.mark.unit
class TestPermissionResourceTypes:
    """Test permission with different resource types"""
    
    def test_permission_works_with_custom_resource_types(self):
        """Test permission works with any resource type (free string)"""
        # Test various resource types
        ticket_perm = PermissionFactory.create(
            resource_type="ticket",
            resource_id="ticket-123",
            action=PermissionAction.UPDATE
        )
        
        invoice_perm = PermissionFactory.create(
            resource_type="invoice",
            resource_id="inv-456",
            action=PermissionAction.READ
        )
        
        deal_perm = PermissionFactory.create(
            resource_type="deal",
            resource_id="deal-789",
            action=PermissionAction.DELETE
        )
        
        # All should work correctly
        assert ticket_perm.allows(PermissionAction.UPDATE, "ticket-123") is True
        assert invoice_perm.allows(PermissionAction.READ, "inv-456") is True
        assert deal_perm.allows(PermissionAction.DELETE, "deal-789") is True
    
    def test_resource_type_is_normalized_to_lowercase(self):
        """Test resource_type is normalized to lowercase"""
        permission = Permission(
            user_id="user-123",
            client_id="client-123",
            resource_type="PROJECT",  # Uppercase
            action=PermissionAction.READ
        )
        
        # Should be normalized to lowercase
        assert permission.resource_type == "project"
    
    def test_resource_type_is_trimmed(self):
        """Test resource_type whitespace is trimmed"""
        permission = Permission(
            user_id="user-123",
            client_id="client-123",
            resource_type="  project  ",  # With spaces
            action=PermissionAction.READ
        )
        
        # Should be trimmed
        assert permission.resource_type == "project"


@pytest.mark.unit
class TestPermissionCreation:
    """Test permission creation and initialization"""
    
    def test_permission_sets_created_at_automatically(self):
        """Test created_at is set automatically"""
        permission = Permission(
            user_id="user-123",
            client_id="client-123",
            resource_type="project",
            action=PermissionAction.READ
        )
        
        assert permission.created_at is not None
        assert isinstance(permission.created_at, datetime)
    
    def test_permission_accepts_custom_created_at(self):
        """Test created_at can be set manually"""
        custom_date = datetime(2023, 1, 1, 12, 0, 0)
        
        permission = Permission(
            user_id="user-123",
            client_id="client-123",
            resource_type="project",
            action=PermissionAction.READ,
            created_at=custom_date
        )
        
        assert permission.created_at == custom_date
    
    def test_permission_stores_granted_by_user_id(self):
        """Test permission stores who granted it"""
        permission = PermissionFactory.create(
            granted_by="admin-456"
        )
        
        assert permission.granted_by == "admin-456"


@pytest.mark.unit
class TestPermissionActions:
    """Test different permission actions"""
    
    def test_create_action_permission(self):
        """Test CREATE action permission"""
        permission = PermissionFactory.create(
            action=PermissionAction.CREATE
        )
        
        assert permission.allows(PermissionAction.CREATE, permission.resource_id) is True
        assert permission.allows(PermissionAction.READ, permission.resource_id) is False
    
    def test_read_action_permission(self):
        """Test READ action permission"""
        permission = PermissionFactory.create(
            action=PermissionAction.READ
        )
        
        assert permission.allows(PermissionAction.READ, permission.resource_id) is True
        assert permission.allows(PermissionAction.UPDATE, permission.resource_id) is False
    
    def test_update_action_permission(self):
        """Test UPDATE action permission"""
        permission = PermissionFactory.create(
            action=PermissionAction.UPDATE
        )
        
        assert permission.allows(PermissionAction.UPDATE, permission.resource_id) is True
        assert permission.allows(PermissionAction.DELETE, permission.resource_id) is False
    
    def test_delete_action_permission(self):
        """Test DELETE action permission"""
        permission = PermissionFactory.create(
            action=PermissionAction.DELETE
        )
        
        assert permission.allows(PermissionAction.DELETE, permission.resource_id) is True
        assert permission.allows(PermissionAction.CREATE, permission.resource_id) is False


@pytest.mark.unit
class TestPermissionMultiTenant:
    """Test permission multi-tenancy"""
    
    def test_permission_belongs_to_client(self):
        """Test permission is scoped to client"""
        permission = PermissionFactory.create(
            client_id="client-abc"
        )
        
        assert permission.client_id == "client-abc"
    
    def test_permission_belongs_to_user(self):
        """Test permission is assigned to specific user"""
        permission = PermissionFactory.create(
            user_id="user-123"
        )
        
        assert permission.user_id == "user-123"

