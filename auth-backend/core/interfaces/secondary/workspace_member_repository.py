"""Workspace Member Repository Interface"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.workspace.workspace_member import WorkspaceMember


class IWorkspaceMemberRepository(ABC):
    """Interface for workspace member data persistence"""
    
    @abstractmethod
    async def save(self, member: WorkspaceMember) -> WorkspaceMember:
        """Save or update workspace member"""
        pass
    
    @abstractmethod
    async def find_by_id(self, member_id: str) -> Optional[WorkspaceMember]:
        """Find workspace member by ID"""
        pass
    
    @abstractmethod
    async def find_by_user_and_workspace(
        self, user_id: str, workspace_id: str
    ) -> Optional[WorkspaceMember]:
        """Find workspace member by user and workspace"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, active_only: bool = True) -> List[WorkspaceMember]:
        """Find all workspaces for a user"""
        pass
    
    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: str, active_only: bool = True
    ) -> List[WorkspaceMember]:
        """Find all members of a workspace"""
        pass
    
    @abstractmethod
    async def delete(self, member_id: str) -> bool:
        """Delete workspace member"""
        pass

