"""Workspace Member Service - Business logic for workspace members"""
import uuid
from datetime import datetime
from typing import List, Optional
from core.domain.workspace.workspace_member import WorkspaceMember
from core.domain.workspace.workspace_role import WorkspaceRole
from core.interfaces.secondary.workspace_member_repository import IWorkspaceMemberRepository
from core.exceptions import NotFoundException, BusinessRuleException


class WorkspaceMemberService:
    """Service for workspace member management"""
    
    def __init__(self, workspace_member_repository: IWorkspaceMemberRepository):
        self.workspace_member_repository = workspace_member_repository
    
    async def add_member(
        self,
        user_id: str,
        workspace_id: str,
        role: WorkspaceRole = WorkspaceRole.USER
    ) -> WorkspaceMember:
        """
        Add user to workspace.
        
        Args:
            user_id: User ID
            workspace_id: Workspace ID
            role: Member role (default: USER)
            
        Returns:
            Workspace member
            
        Raises:
            BusinessRuleException: If user is already a member
        """
        # Check if already exists
        existing = await self.workspace_member_repository.find_by_user_and_workspace(
            user_id, workspace_id
        )
        
        if existing:
            raise BusinessRuleException(
                f"User {user_id} is already a member of workspace {workspace_id}"
            )
        
        member = WorkspaceMember(
            id=str(uuid.uuid4()),
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            active=True,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        member.validate()
        
        return await self.workspace_member_repository.save(member)
    
    async def get_member(
        self, user_id: str, workspace_id: str
    ) -> Optional[WorkspaceMember]:
        """Get workspace member"""
        return await self.workspace_member_repository.find_by_user_and_workspace(
            user_id, workspace_id
        )
    
    async def get_user_workspaces(
        self, user_id: str, active_only: bool = True
    ) -> List[WorkspaceMember]:
        """Get all workspaces for a user"""
        return await self.workspace_member_repository.find_by_user(user_id, active_only)
    
    async def get_workspace_members(
        self, workspace_id: str, active_only: bool = True
    ) -> List[WorkspaceMember]:
        """Get all members of a workspace"""
        return await self.workspace_member_repository.find_by_workspace(
            workspace_id, active_only
        )
    
    async def update_member_role(
        self, user_id: str, workspace_id: str, new_role: WorkspaceRole
    ) -> WorkspaceMember:
        """
        Update member's role in workspace.
        
        Args:
            user_id: User ID
            workspace_id: Workspace ID
            new_role: New role
            
        Returns:
            Updated workspace member
            
        Raises:
            NotFoundException: If member not found
        """
        member = await self.workspace_member_repository.find_by_user_and_workspace(
            user_id, workspace_id
        )
        
        if not member:
            raise NotFoundException(
                f"Member not found: user {user_id} in workspace {workspace_id}"
            )
        
        member.update_role(new_role)
        member.updated_at = datetime.utcnow()
        
        return await self.workspace_member_repository.save(member)
    
    async def remove_member(self, user_id: str, workspace_id: str) -> bool:
        """
        Remove user from workspace.
        
        Args:
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if removed
            
        Raises:
            NotFoundException: If member not found
        """
        member = await self.workspace_member_repository.find_by_user_and_workspace(
            user_id, workspace_id
        )
        
        if not member:
            raise NotFoundException(
                f"Member not found: user {user_id} in workspace {workspace_id}"
            )
        
        return await self.workspace_member_repository.delete(member.id)
    
    async def deactivate_member(self, user_id: str, workspace_id: str) -> WorkspaceMember:
        """Deactivate member (soft delete)"""
        member = await self.workspace_member_repository.find_by_user_and_workspace(
            user_id, workspace_id
        )
        
        if not member:
            raise NotFoundException(
                f"Member not found: user {user_id} in workspace {workspace_id}"
            )
        
        member.deactivate()
        member.updated_at = datetime.utcnow()
        
        return await self.workspace_member_repository.save(member)
    
    async def activate_member(self, user_id: str, workspace_id: str) -> WorkspaceMember:
        """Activate member"""
        member = await self.workspace_member_repository.find_by_user_and_workspace(
            user_id, workspace_id
        )
        
        if not member:
            raise NotFoundException(
                f"Member not found: user {user_id} in workspace {workspace_id}"
            )
        
        member.activate()
        member.updated_at = datetime.utcnow()
        
        return await self.workspace_member_repository.save(member)

