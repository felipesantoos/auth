"""
Workspace Member Mapper
Maps between domain WorkspaceMember and database DBWorkspaceMember
"""
from typing import Optional
from core.domain.workspace.workspace_member import WorkspaceMember
from core.domain.workspace.workspace_role import WorkspaceRole
from infra.database.models.workspace_member import DBWorkspaceMember


class WorkspaceMemberMapper:
    """Mapper for WorkspaceMember domain model and DBWorkspaceMember database model"""
    
    @staticmethod
    def to_domain(db_member: DBWorkspaceMember) -> WorkspaceMember:
        """
        Convert database model to domain model.
        
        Args:
            db_member: Database workspace member model
            
        Returns:
            Domain workspace member model
        """
        return WorkspaceMember(
            id=db_member.id,
            user_id=db_member.user_id,
            workspace_id=db_member.workspace_id,
            role=WorkspaceRole(db_member.role),
            active=db_member.active,
            invited_at=db_member.invited_at,
            joined_at=db_member.joined_at,
            created_at=db_member.created_at,
            updated_at=db_member.updated_at
        )
    
    @staticmethod
    def to_db(member: WorkspaceMember) -> DBWorkspaceMember:
        """
        Convert domain model to database model.
        
        Args:
            member: Domain workspace member model
            
        Returns:
            Database workspace member model
        """
        return DBWorkspaceMember(
            id=member.id,
            user_id=member.user_id,
            workspace_id=member.workspace_id,
            role=member.role.value,
            active=member.active,
            invited_at=member.invited_at,
            joined_at=member.joined_at,
            created_at=member.created_at,
            updated_at=member.updated_at
        )
    
    @staticmethod
    def update_db_from_domain(db_member: DBWorkspaceMember, member: WorkspaceMember) -> DBWorkspaceMember:
        """
        Update database model from domain model.
        
        Args:
            db_member: Existing database workspace member model
            member: Domain workspace member model with new values
            
        Returns:
            Updated database workspace member model
        """
        db_member.role = member.role.value
        db_member.active = member.active
        db_member.invited_at = member.invited_at
        db_member.joined_at = member.joined_at
        db_member.updated_at = member.updated_at
        
        return db_member

