"""Integration tests for WorkspaceRepository"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.workspace_repository import WorkspaceRepository
from tests.factories.workspace_factory import WorkspaceFactory
from core.exceptions import NotFoundException, DuplicateEntityException


@pytest.mark.asyncio
class TestWorkspaceRepository:
    """Test suite for WorkspaceRepository"""
    
    async def test_save_new_workspace(self, db_session: AsyncSession):
        """Test saving a new workspace"""
        repository = WorkspaceRepository(db_session)
        workspace = WorkspaceFactory.create_workspace(
            id=None,
            name="New Workspace",
            slug="new-workspace"
        )
        
        saved = await repository.save(workspace)
        
        assert saved.id is not None
        assert saved.name == "New Workspace"
        assert saved.slug == "new-workspace"
    
    async def test_save_duplicate_slug(self, db_session: AsyncSession):
        """Test saving workspace with duplicate slug fails"""
        repository = WorkspaceRepository(db_session)
        
        # Create first workspace
        workspace1 = WorkspaceFactory.create_workspace(
            id=None,
            name="Workspace 1",
            slug="same-slug"
        )
        await repository.save(workspace1)
        
        # Try to create second with same slug
        workspace2 = WorkspaceFactory.create_workspace(
            id=None,
            name="Workspace 2",
            slug="same-slug"
        )
        
        with pytest.raises(DuplicateEntityException):
            await repository.save(workspace2)
    
    async def test_find_by_id(self, db_session: AsyncSession):
        """Test finding workspace by ID"""
        repository = WorkspaceRepository(db_session)
        workspace = WorkspaceFactory.create_workspace(id=None)
        saved = await repository.save(workspace)
        
        found = await repository.find_by_id(saved.id)
        
        assert found is not None
        assert found.id == saved.id
        assert found.name == saved.name
    
    async def test_find_by_id_not_found(self, db_session: AsyncSession):
        """Test finding non-existent workspace"""
        repository = WorkspaceRepository(db_session)
        
        found = await repository.find_by_id("non-existent-id")
        
        assert found is None
    
    async def test_find_by_slug(self, db_session: AsyncSession):
        """Test finding workspace by slug"""
        repository = WorkspaceRepository(db_session)
        workspace = WorkspaceFactory.create_workspace(
            id=None,
            slug="unique-slug"
        )
        saved = await repository.save(workspace)
        
        found = await repository.find_by_slug("unique-slug")
        
        assert found is not None
        assert found.id == saved.id
        assert found.slug == "unique-slug"
    
    async def test_find_all(self, db_session: AsyncSession):
        """Test finding all workspaces"""
        repository = WorkspaceRepository(db_session)
        
        # Create multiple workspaces
        ws1 = WorkspaceFactory.create_workspace(id=None, slug="ws-1")
        ws2 = WorkspaceFactory.create_workspace(id=None, slug="ws-2")
        
        await repository.save(ws1)
        await repository.save(ws2)
        
        workspaces = await repository.find_all(active_only=True)
        
        assert len(workspaces) >= 2
    
    async def test_delete_workspace(self, db_session: AsyncSession):
        """Test deleting workspace"""
        repository = WorkspaceRepository(db_session)
        workspace = WorkspaceFactory.create_workspace(id=None)
        saved = await repository.save(workspace)
        
        result = await repository.delete(saved.id)
        
        assert result is True
        
        # Verify it's deleted
        found = await repository.find_by_id(saved.id)
        assert found is None

