"""Workspace Service - Business logic for workspaces"""
import uuid
from datetime import datetime
from typing import List, Optional
from core.domain.workspace.workspace import Workspace
from core.interfaces.secondary.workspace_repository import IWorkspaceRepository
from core.exceptions import NotFoundException, ValidationException


class WorkspaceService:
    """Service for workspace management"""
    
    def __init__(self, workspace_repository: IWorkspaceRepository):
        self.workspace_repository = workspace_repository
    
    async def create_workspace(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> Workspace:
        """
        Create a new workspace.
        
        Args:
            name: Workspace name
            slug: URL-friendly slug (auto-generated if not provided)
            description: Workspace description
            settings: Workspace settings (JSON)
            
        Returns:
            Created workspace
            
        Raises:
            ValidationException: If validation fails
        """
        # Auto-generate slug if not provided
        if not slug:
            slug = Workspace.generate_slug_from_name(name)
        
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            settings=settings or {},
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Validate
        workspace.validate()
        
        # Save
        return await self.workspace_repository.save(workspace)
    
    async def get_workspace(self, workspace_id: str) -> Workspace:
        """
        Get workspace by ID.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            Workspace
            
        Raises:
            NotFoundException: If workspace not found
        """
        workspace = await self.workspace_repository.find_by_id(workspace_id)
        
        if not workspace:
            raise NotFoundException(f"Workspace not found: {workspace_id}")
        
        return workspace
    
    async def get_workspace_by_slug(self, slug: str) -> Workspace:
        """
        Get workspace by slug.
        
        Args:
            slug: Workspace slug
            
        Returns:
            Workspace
            
        Raises:
            NotFoundException: If workspace not found
        """
        workspace = await self.workspace_repository.find_by_slug(slug)
        
        if not workspace:
            raise NotFoundException(f"Workspace not found: {slug}")
        
        return workspace
    
    async def list_workspaces(self, active_only: bool = True) -> List[Workspace]:
        """
        List all workspaces.
        
        Args:
            active_only: Only return active workspaces
            
        Returns:
            List of workspaces
        """
        return await self.workspace_repository.find_all(active_only=active_only)
    
    async def update_workspace(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> Workspace:
        """
        Update workspace.
        
        Args:
            workspace_id: Workspace ID
            name: New name
            slug: New slug
            description: New description
            settings: New settings
            
        Returns:
            Updated workspace
            
        Raises:
            NotFoundException: If workspace not found
            ValidationException: If validation fails
        """
        workspace = await self.get_workspace(workspace_id)
        
        if name:
            workspace.update_name(name)
        
        if slug:
            workspace.update_slug(slug)
        
        if description is not None:
            workspace.update_description(description)
        
        if settings is not None:
            workspace.update_settings(settings)
        
        workspace.updated_at = datetime.utcnow()
        workspace.validate()
        
        return await self.workspace_repository.save(workspace)
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete workspace.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundException: If workspace not found
        """
        workspace = await self.get_workspace(workspace_id)
        return await self.workspace_repository.delete(workspace.id)
    
    async def activate_workspace(self, workspace_id: str) -> Workspace:
        """Activate workspace"""
        workspace = await self.get_workspace(workspace_id)
        workspace.activate()
        workspace.updated_at = datetime.utcnow()
        return await self.workspace_repository.save(workspace)
    
    async def deactivate_workspace(self, workspace_id: str) -> Workspace:
        """Deactivate workspace"""
        workspace = await self.get_workspace(workspace_id)
        workspace.deactivate()
        workspace.updated_at = datetime.utcnow()
        return await self.workspace_repository.save(workspace)

