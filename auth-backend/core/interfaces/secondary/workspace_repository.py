"""Workspace Repository Interface"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.workspace.workspace import Workspace


class IWorkspaceRepository(ABC):
    """Interface for workspace data persistence"""
    
    @abstractmethod
    async def save(self, workspace: Workspace) -> Workspace:
        """Save or update workspace"""
        pass
    
    @abstractmethod
    async def find_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """Find workspace by ID"""
        pass
    
    @abstractmethod
    async def find_by_slug(self, slug: str) -> Optional[Workspace]:
        """Find workspace by slug (unique identifier)"""
        pass
    
    @abstractmethod
    async def find_all(self, active_only: bool = True) -> List[Workspace]:
        """Find all workspaces"""
        pass
    
    @abstractmethod
    async def delete(self, workspace_id: str) -> bool:
        """Delete workspace"""
        pass

