"""Unit tests for WorkspaceService"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from core.services.workspace.workspace_service import WorkspaceService
from core.domain.workspace.workspace import Workspace
from tests.factories.workspace_factory import WorkspaceFactory
from core.exceptions import NotFoundException


@pytest.mark.asyncio
class TestWorkspaceService:
    """Test suite for WorkspaceService"""
    
    async def test_create_workspace(self):
        """Test creating a workspace"""
        # Mock repository
        mock_repo = AsyncMock()
        service = WorkspaceService(mock_repo)
        
        # Mock save to return the workspace
        expected_workspace = WorkspaceFactory.create_workspace()
        mock_repo.save.return_value = expected_workspace
        
        # Create workspace
        result = await service.create_workspace(
            name="Test Workspace",
            slug="test-workspace"
        )
        
        # Verify
        assert result is not None
        mock_repo.save.assert_called_once()
    
    async def test_create_workspace_auto_slug(self):
        """Test creating workspace with auto-generated slug"""
        mock_repo = AsyncMock()
        service = WorkspaceService(mock_repo)
        
        expected_workspace = WorkspaceFactory.create_workspace(slug="my-company")
        mock_repo.save.return_value = expected_workspace
        
        # Create without slug
        result = await service.create_workspace(name="My Company")
        
        # Verify slug was generated
        mock_repo.save.assert_called_once()
        saved_workspace = mock_repo.save.call_args[0][0]
        assert saved_workspace.slug is not None
    
    async def test_get_workspace(self):
        """Test getting workspace by ID"""
        mock_repo = AsyncMock()
        service = WorkspaceService(mock_repo)
        
        expected = WorkspaceFactory.create_workspace()
        mock_repo.find_by_id.return_value = expected
        
        result = await service.get_workspace("test-id")
        
        assert result == expected
        mock_repo.find_by_id.assert_called_once_with("test-id")
    
    async def test_get_workspace_not_found(self):
        """Test getting non-existent workspace"""
        mock_repo = AsyncMock()
        service = WorkspaceService(mock_repo)
        
        mock_repo.find_by_id.return_value = None
        
        with pytest.raises(NotFoundException):
            await service.get_workspace("non-existent")
    
    async def test_update_workspace(self):
        """Test updating workspace"""
        mock_repo = AsyncMock()
        service = WorkspaceService(mock_repo)
        
        existing = WorkspaceFactory.create_workspace(name="Old Name")
        updated = WorkspaceFactory.create_workspace(name="New Name")
        
        mock_repo.find_by_id.return_value = existing
        mock_repo.save.return_value = updated
        
        result = await service.update_workspace(
            workspace_id="test-id",
            name="New Name"
        )
        
        assert result.name == "New Name"
    
    async def test_delete_workspace(self):
        """Test deleting workspace"""
        mock_repo = AsyncMock()
        service = WorkspaceService(mock_repo)
        
        existing = WorkspaceFactory.create_workspace()
        mock_repo.find_by_id.return_value = existing
        mock_repo.delete.return_value = True
        
        result = await service.delete_workspace("test-id")
        
        assert result is True
        mock_repo.delete.assert_called_once()

