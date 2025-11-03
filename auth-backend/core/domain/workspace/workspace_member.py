"""
Workspace Member Domain Model
Represents a user's membership in a workspace
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from .workspace_role import WorkspaceRole
from core.exceptions import MissingRequiredFieldException


@dataclass
class WorkspaceMember:
    """
    Domain model for workspace membership.
    
    This is pure business logic with no framework dependencies.
    Represents the N:M relationship between User and Workspace.
    Each member can have a different role per workspace.
    """
    id: Optional[str]
    user_id: str
    workspace_id: str
    role: WorkspaceRole
    active: bool = True
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate workspace member according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
        """
        # Required fields
        if not self.user_id or not self.user_id.strip():
            raise MissingRequiredFieldException("user_id")
        
        if not self.workspace_id or not self.workspace_id.strip():
            raise MissingRequiredFieldException("workspace_id")
        
        if not self.role:
            raise MissingRequiredFieldException("role")
    
    def activate(self) -> None:
        """Business operation to activate membership"""
        self.active = True
    
    def deactivate(self) -> None:
        """Business operation to deactivate membership"""
        self.active = False
    
    def is_admin(self) -> bool:
        """Check if member has admin role in this workspace"""
        return self.role == WorkspaceRole.ADMIN
    
    def is_manager(self) -> bool:
        """Check if member has manager role in this workspace"""
        return self.role == WorkspaceRole.MANAGER
    
    def can_manage_users(self) -> bool:
        """Check if member can manage other users in this workspace"""
        return self.role in [WorkspaceRole.ADMIN, WorkspaceRole.MANAGER]
    
    def can_manage_workspace(self) -> bool:
        """Check if member can manage workspace settings"""
        return self.role == WorkspaceRole.ADMIN
    
    def update_role(self, new_role: WorkspaceRole) -> None:
        """
        Update member's role in workspace.
        
        Args:
            new_role: New role for the member
            
        Raises:
            MissingRequiredFieldException: If role is empty
        """
        if not new_role:
            raise MissingRequiredFieldException("role")
        
        self.role = new_role
    
    def mark_as_joined(self) -> None:
        """Mark member as having joined the workspace"""
        if not self.joined_at:
            self.joined_at = datetime.utcnow()
    
    def mark_as_invited(self) -> None:
        """Mark when member was invited"""
        if not self.invited_at:
            self.invited_at = datetime.utcnow()

