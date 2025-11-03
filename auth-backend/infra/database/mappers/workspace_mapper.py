"""
Workspace Mapper
Maps between domain Workspace and database DBWorkspace
"""
from typing import Optional
from core.domain.workspace.workspace import Workspace
from infra.database.models.workspace import DBWorkspace


class WorkspaceMapper:
    """Mapper for Workspace domain model and DBWorkspace database model"""
    
    @staticmethod
    def to_domain(db_workspace: DBWorkspace) -> Workspace:
        """
        Convert database model to domain model.
        
        Args:
            db_workspace: Database workspace model
            
        Returns:
            Domain workspace model
        """
        return Workspace(
            id=db_workspace.id,
            name=db_workspace.name,
            slug=db_workspace.slug,
            description=db_workspace.description,
            settings=db_workspace.settings,
            active=db_workspace.active,
            created_at=db_workspace.created_at,
            updated_at=db_workspace.updated_at
        )
    
    @staticmethod
    def to_db(workspace: Workspace) -> DBWorkspace:
        """
        Convert domain model to database model.
        
        Args:
            workspace: Domain workspace model
            
        Returns:
            Database workspace model
        """
        return DBWorkspace(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            active=workspace.active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )
    
    @staticmethod
    def update_db_from_domain(db_workspace: DBWorkspace, workspace: Workspace) -> DBWorkspace:
        """
        Update database model from domain model.
        
        Args:
            db_workspace: Existing database workspace model
            workspace: Domain workspace model with new values
            
        Returns:
            Updated database workspace model
        """
        db_workspace.name = workspace.name
        db_workspace.slug = workspace.slug
        db_workspace.description = workspace.description
        db_workspace.settings = workspace.settings
        db_workspace.active = workspace.active
        db_workspace.updated_at = workspace.updated_at
        
        return db_workspace

