"""
Test Permission Service
"""
import pytest
from unittest.mock import Mock, AsyncMock
from core.services.auth.permission_service import PermissionService
from core.domain.auth.permission import Permission, PermissionAction, ResourceType
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole


@pytest.fixture
def mock_repository():
    """Mock permission repository"""
    repo = Mock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.find_by_user = AsyncMock()
    repo.find_by_user_and_resource_type = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def admin_user():
    """Create admin user"""
    return AppUser(
        id="admin-123",
        username="admin",
        email="admin@example.com",
        name="Admin User",
        role=UserRole.ADMIN,
        client_id="client-123",
        _password_hash="hashed",
        active=True
    )


@pytest.fixture
def regular_user():
    """Create regular user"""
    return AppUser(
        id="user-123",
        username="user",
        email="user@example.com",
        name="Regular User",
        role=UserRole.USER,
        client_id="client-123",
        _password_hash="hashed",
        active=True
    )


class TestPermissionService:
    """Test permission service"""
    
    @pytest.mark.asyncio
    async def test_admin_bypasses_permission_check(self, mock_repository, admin_user):
        """Admin users should bypass all permission checks"""
        service = PermissionService(mock_repository)
        
        # Admin should have permission without checking repository
        has_perm = await service.has_permission(
            admin_user,
            ResourceType.PROJECT,
            PermissionAction.DELETE,
            "project-123"
        )
        
        assert has_perm is True
        # Repository should not be called
        assert not mock_repository.find_by_user_and_resource_type.called
    
    @pytest.mark.asyncio
    async def test_user_with_permission(self, mock_repository, regular_user):
        """User with permission should be granted access"""
        # Mock permission that allows READ on project-123
        mock_permission = Permission(
            id="perm-123",
            user_id="user-123",
            client_id="client-123",
            resource_type=ResourceType.PROJECT,
            resource_id="project-123",
            action=PermissionAction.READ
        )
        mock_repository.find_by_user_and_resource_type.return_value = [mock_permission]
        
        service = PermissionService(mock_repository)
        
        has_perm = await service.has_permission(
            regular_user,
            ResourceType.PROJECT,
            PermissionAction.READ,
            "project-123"
        )
        
        assert has_perm is True
    
    @pytest.mark.asyncio
    async def test_user_without_permission(self, mock_repository, regular_user):
        """User without permission should be denied"""
        mock_repository.find_by_user_and_resource_type.return_value = []
        
        service = PermissionService(mock_repository)
        
        has_perm = await service.has_permission(
            regular_user,
            ResourceType.PROJECT,
            PermissionAction.DELETE,
            "project-123"
        )
        
        assert has_perm is False
    
    @pytest.mark.asyncio
    async def test_manage_permission_allows_all_actions(self, mock_repository, regular_user):
        """MANAGE permission should allow all actions"""
        # Mock MANAGE permission
        mock_permission = Permission(
            id="perm-123",
            user_id="user-123",
            client_id="client-123",
            resource_type=ResourceType.PROJECT,
            resource_id="project-123",
            action=PermissionAction.MANAGE
        )
        mock_repository.find_by_user_and_resource_type.return_value = [mock_permission]
        
        service = PermissionService(mock_repository)
        
        # Should allow DELETE even though permission is MANAGE
        has_perm = await service.has_permission(
            regular_user,
            ResourceType.PROJECT,
            PermissionAction.DELETE,
            "project-123"
        )
        
        assert has_perm is True
    
    @pytest.mark.asyncio
    async def test_grant_permission_as_admin(self, mock_repository, admin_user):
        """Admin should be able to grant permissions"""
        mock_repository.save.return_value = Permission(
            id="perm-456",
            user_id="user-123",
            client_id="client-123",
            resource_type=ResourceType.PROJECT,
            resource_id="project-123",
            action=PermissionAction.UPDATE,
            granted_by="admin-123"
        )
        
        service = PermissionService(mock_repository)
        
        permission = await service.grant_permission(
            granter=admin_user,
            user_id="user-123",
            resource_type=ResourceType.PROJECT,
            action=PermissionAction.UPDATE,
            resource_id="project-123"
        )
        
        assert permission.id == "perm-456"
        assert permission.granted_by == "admin-123"
        assert mock_repository.save.called
    
    @pytest.mark.asyncio
    async def test_revoke_permission_as_admin(self, mock_repository, admin_user):
        """Admin should be able to revoke permissions"""
        mock_permission = Permission(
            id="perm-123",
            user_id="user-123",
            client_id="client-123",
            resource_type=ResourceType.PROJECT,
            resource_id="project-123",
            action=PermissionAction.READ,
            granted_by="admin-123"
        )
        mock_repository.find_by_id.return_value = mock_permission
        mock_repository.delete.return_value = True
        
        service = PermissionService(mock_repository)
        
        result = await service.revoke_permission(admin_user, "perm-123")
        
        assert result is True
        assert mock_repository.delete.called

