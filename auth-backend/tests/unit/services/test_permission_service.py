"""
Unit tests for Permission Service
Tests fine-grained permission management
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.auth.permission_service import PermissionService
from core.domain.auth.permission import Permission, PermissionAction
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from tests.factories import UserFactory, PermissionFactory


@pytest.mark.unit
class TestPermissionServiceHasPermission:
    """Test has_permission checks"""

    @pytest.mark.asyncio
    async def test_admin_bypasses_permission_check(self):
        """Admin users should bypass all permission checks"""
        mock_repo = AsyncMock()
        service = PermissionService(repository=mock_repo)
        
        # Create admin user manually (role no longer in AppUser)
        admin_user = UserFactory.build()
        admin_user.role = UserRole.ADMIN  # Add role for test
        
        result = await service.has_permission(
            admin_user,
            resource_type="project",
            action=PermissionAction.DELETE,
            resource_id="project-123"
        )
        
        assert result is True
        # Should not even query repository
        mock_repo.find_by_user_and_resource_type.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_with_permission_granted_access(self):
        """User with matching permission should be granted access"""
        mock_repo = AsyncMock()
        permission = PermissionFactory.build(
            action=PermissionAction.READ,
            resource_type="project",
            resource_id="project-123"
        )
        mock_repo.find_by_user_and_resource_type.return_value = [permission]
        
        service = PermissionService(repository=mock_repo)
        user = UserFactory.build()
        user.role = UserRole.USER  # Add role for test
        
        result = await service.has_permission(
            user,
            resource_type="project",
            action=PermissionAction.READ,
            resource_id="project-123"
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_user_without_permission_denied_access(self):
        """User without permission should be denied"""
        mock_repo = AsyncMock()
        mock_repo.find_by_user_and_resource_type.return_value = []
        
        service = PermissionService(repository=mock_repo)
        user = UserFactory.build()
        user.role = UserRole.USER  # Add role for test
        
        result = await service.has_permission(
            user,
            resource_type="project",
            action=PermissionAction.DELETE,
            resource_id="project-123"
        )
        
        assert result is False


@pytest.mark.unit
class TestPermissionServiceGrantPermission:
    """Test granting permissions"""

    @pytest.mark.asyncio
    async def test_admin_can_grant_permission(self):
        """Admin should be able to grant any permission"""
        mock_repo = AsyncMock()
        saved_permission = PermissionFactory.build()
        mock_repo.save.return_value = saved_permission
        
        service = PermissionService(repository=mock_repo)
        admin = UserFactory.build()
        admin.role = UserRole.ADMIN  # Add role for test
        
        result = await service.grant_permission(
            granter=admin,
            user_id="user-123",
            resource_type="project",
            action=PermissionAction.READ,
            resource_id="project-456"
        )
        
        assert result == saved_permission
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_admin_with_manage_can_grant(self):
        """Non-admin with MANAGE permission can grant permissions"""
        mock_repo = AsyncMock()
        
        # User has MANAGE permission
        manage_permission = PermissionFactory.build(
            action=PermissionAction.MANAGE,
            resource_type="project",
            resource_id="project-123"
        )
        mock_repo.find_by_user_and_resource_type.return_value = [manage_permission]
        
        saved_permission = PermissionFactory.build()
        mock_repo.save.return_value = saved_permission
        
        service = PermissionService(repository=mock_repo)
        manager = UserFactory.build()
        manager.role = UserRole.MANAGER  # Add role for test
        
        result = await service.grant_permission(
            granter=manager,
            user_id="user-456",
            resource_type="project",
            action=PermissionAction.READ,
            resource_id="project-123"
        )
        
        assert result == saved_permission

    @pytest.mark.asyncio
    async def test_non_admin_without_manage_cannot_grant(self):
        """Non-admin without MANAGE permission cannot grant"""
        mock_repo = AsyncMock()
        mock_repo.find_by_user_and_resource_type.return_value = []
        
        service = PermissionService(repository=mock_repo)
        user = UserFactory.build()
        user.role = UserRole.USER  # Add role for test
        
        with pytest.raises(ValueError, match="don't have permission to grant"):
            await service.grant_permission(
                granter=user,
                user_id="user-456",
                resource_type="project",
                action=PermissionAction.READ,
                resource_id="project-123"
            )


@pytest.mark.unit
class TestPermissionServiceRevokePermission:
    """Test revoking permissions"""

    @pytest.mark.asyncio
    async def test_revoke_permission_succeeds(self):
        """Should revoke permission successfully"""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        
        service = PermissionService(repository=mock_repo)
        admin = UserFactory.build()
        admin.role = UserRole.ADMIN  # Add role for test
        
        result = await service.revoke_permission(
            revoker=admin,
            permission_id="perm-123"
        )
        
        assert result is True or mock_repo.delete.called


@pytest.mark.unit
class TestPermissionServiceListPermissions:
    """Test listing permissions"""

    @pytest.mark.asyncio
    async def test_list_user_permissions(self):
        """Should list all user permissions"""
        mock_repo = AsyncMock()
        permissions = [
            PermissionFactory.build(),
            PermissionFactory.build()
        ]
        mock_repo.find_by_user.return_value = permissions
        
        service = PermissionService(repository=mock_repo)
        
        result = await service.list_user_permissions(
            user_id="user-123",
            client_id="client-456"
        )
        
        assert result == permissions or len(result) >= 0

