"""
Tests for PermissionRepository
Tests database operations for permission entity
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.permission_repository import PermissionRepository
from core.domain.auth.permission import PermissionAction
from tests.factories import PermissionFactory, UserFactory


@pytest.mark.integration
class TestPermissionRepositorySave:
    """Test saving permissions"""
    
    @pytest.mark.asyncio
    async def test_save_new_permission(self, db_session: AsyncSession):
        """Test saving a new permission"""
        repository = PermissionRepository(db_session)
        permission = PermissionFactory.create()
        
        saved_permission = await repository.save(permission)
        
        assert saved_permission.id is not None
        assert saved_permission.user_id == permission.user_id
        assert saved_permission.resource_type == permission.resource_type
    
    @pytest.mark.asyncio
    async def test_save_updates_existing_permission(self, db_session: AsyncSession):
        """Test saving existing permission updates it"""
        repository = PermissionRepository(db_session)
        
        # Create permission
        permission = PermissionFactory.create(action=PermissionAction.READ)
        saved_permission = await repository.save(permission)
        
        # Update permission
        saved_permission.action = PermissionAction.WRITE
        updated_permission = await repository.save(saved_permission)
        
        assert updated_permission.id == saved_permission.id
        assert updated_permission.action == PermissionAction.WRITE


@pytest.mark.integration
class TestPermissionRepositoryFind:
    """Test finding permissions"""
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_permission(self, db_session: AsyncSession):
        """Test find_by_id returns existing permission"""
        repository = PermissionRepository(db_session)
        
        # Create permission
        permission = PermissionFactory.create()
        saved_permission = await repository.save(permission)
        
        # Find permission
        found_permission = await repository.find_by_id(saved_permission.id)
        
        assert found_permission is not None
        assert found_permission.id == saved_permission.id
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test find_by_id returns None for nonexistent permission"""
        repository = PermissionRepository(db_session)
        
        found_permission = await repository.find_by_id("nonexistent-id")
        
        assert found_permission is None
    
    @pytest.mark.asyncio
    async def test_find_by_user_returns_user_permissions(self, db_session: AsyncSession):
        """Test find_by_user returns all permissions for a user"""
        repository = PermissionRepository(db_session)
        
        user_id = "user-123"
        client_id = "client-456"
        
        # Create multiple permissions for user
        perm1 = PermissionFactory.create(
            user_id=user_id,
            client_id=client_id,
            resource_type="project"
        )
        perm2 = PermissionFactory.create(
            user_id=user_id,
            client_id=client_id,
            resource_type="ticket"
        )
        await repository.save(perm1)
        await repository.save(perm2)
        
        # Find all permissions for user
        permissions = await repository.find_by_user(user_id, client_id)
        
        assert len(permissions) >= 2
        assert all(p.user_id == user_id for p in permissions)
    
    @pytest.mark.asyncio
    async def test_find_by_user_respects_client_isolation(self, db_session: AsyncSession):
        """Test find_by_user respects multi-tenant isolation"""
        repository = PermissionRepository(db_session)
        
        # Create permission in client A
        perm_a = PermissionFactory.create(
            user_id="user-123",
            client_id="client-a"
        )
        await repository.save(perm_a)
        
        # Find in client B
        permissions = await repository.find_by_user("user-123", "client-b")
        
        # Should not find permission from different client
        assert len(permissions) == 0
    
    @pytest.mark.asyncio
    async def test_find_by_user_and_resource_type(self, db_session: AsyncSession):
        """Test finding permissions by user and resource type"""
        repository = PermissionRepository(db_session)
        
        user_id = "user-123"
        client_id = "client-456"
        
        # Create permissions for different resource types
        project_perm = PermissionFactory.create(
            user_id=user_id,
            client_id=client_id,
            resource_type="project"
        )
        ticket_perm = PermissionFactory.create(
            user_id=user_id,
            client_id=client_id,
            resource_type="ticket"
        )
        await repository.save(project_perm)
        await repository.save(ticket_perm)
        
        # Find only project permissions
        permissions = await repository.find_by_user_and_resource_type(
            user_id,
            client_id,
            "project"
        )
        
        assert len(permissions) >= 1
        assert all(p.resource_type == "project" for p in permissions)


@pytest.mark.integration
class TestPermissionRepositoryDelete:
    """Test deleting permissions"""
    
    @pytest.mark.asyncio
    async def test_delete_existing_permission(self, db_session: AsyncSession):
        """Test deleting existing permission"""
        repository = PermissionRepository(db_session)
        
        # Create permission
        permission = PermissionFactory.create()
        saved_permission = await repository.save(permission)
        
        # Delete permission
        result = await repository.delete(saved_permission.id)
        
        assert result is True
        
        # Verify permission is deleted
        found_permission = await repository.find_by_id(saved_permission.id)
        assert found_permission is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_permission_returns_false(self, db_session: AsyncSession):
        """Test deleting nonexistent permission returns False"""
        repository = PermissionRepository(db_session)
        
        result = await repository.delete("nonexistent-id")
        
        assert result is False


@pytest.mark.integration
class TestPermissionRepositoryMultiTenant:
    """Test multi-tenant isolation"""
    
    @pytest.mark.asyncio
    async def test_permissions_isolated_by_client(self, db_session: AsyncSession):
        """Test permissions are properly isolated by client_id"""
        repository = PermissionRepository(db_session)
        
        # Create permissions for different clients
        perm_client_a = PermissionFactory.create(
            user_id="user-123",
            client_id="client-a",
            resource_type="project"
        )
        perm_client_b = PermissionFactory.create(
            user_id="user-123",
            client_id="client-b",
            resource_type="project"
        )
        await repository.save(perm_client_a)
        await repository.save(perm_client_b)
        
        # Find permissions for client A
        perms_a = await repository.find_by_user("user-123", "client-a")
        
        # Find permissions for client B
        perms_b = await repository.find_by_user("user-123", "client-b")
        
        # Each client should only see their own permissions
        assert all(p.client_id == "client-a" for p in perms_a)
        assert all(p.client_id == "client-b" for p in perms_b)
        
        # Permissions should be different
        perm_a_ids = {p.id for p in perms_a}
        perm_b_ids = {p.id for p in perms_b}
        assert len(perm_a_ids & perm_b_ids) == 0  # No overlap

