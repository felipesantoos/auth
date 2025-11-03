"""Workspace Repository Implementation"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from core.domain.workspace.workspace import Workspace
from core.interfaces.secondary.workspace_repository import IWorkspaceRepository
from infra.database.models.workspace import DBWorkspace
from infra.database.mappers.workspace_mapper import WorkspaceMapper
from core.exceptions import DuplicateEntityException, NotFoundException


class WorkspaceRepository(IWorkspaceRepository):
    """PostgreSQL implementation of workspace repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = WorkspaceMapper()
    
    async def save(self, workspace: Workspace) -> Workspace:
        """Save or update workspace"""
        try:
            if workspace.id:
                # Update existing
                result = await self.session.execute(
                    select(DBWorkspace).where(DBWorkspace.id == workspace.id)
                )
                db_workspace = result.scalar_one_or_none()
                
                if not db_workspace:
                    raise NotFoundException(f"Workspace not found: {workspace.id}")
                
                db_workspace = self.mapper.update_db_from_domain(db_workspace, workspace)
            else:
                # Create new
                db_workspace = self.mapper.to_db(workspace)
                self.session.add(db_workspace)
            
            await self.session.flush()
            await self.session.refresh(db_workspace)
            
            return self.mapper.to_domain(db_workspace)
            
        except IntegrityError as e:
            await self.session.rollback()
            if 'uq_workspace_slug' in str(e) or 'slug' in str(e):
                raise DuplicateEntityException(f"Workspace slug already exists: {workspace.slug}")
            raise
    
    async def find_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """Find workspace by ID"""
        result = await self.session.execute(
            select(DBWorkspace).where(DBWorkspace.id == workspace_id)
        )
        db_workspace = result.scalar_one_or_none()
        
        return self.mapper.to_domain(db_workspace) if db_workspace else None
    
    async def find_by_slug(self, slug: str) -> Optional[Workspace]:
        """Find workspace by slug"""
        result = await self.session.execute(
            select(DBWorkspace).where(DBWorkspace.slug == slug)
        )
        db_workspace = result.scalar_one_or_none()
        
        return self.mapper.to_domain(db_workspace) if db_workspace else None
    
    async def find_all(self, active_only: bool = True) -> List[Workspace]:
        """Find all workspaces"""
        query = select(DBWorkspace)
        
        if active_only:
            query = query.where(DBWorkspace.active == True)
        
        result = await self.session.execute(query.order_by(DBWorkspace.created_at.desc()))
        db_workspaces = result.scalars().all()
        
        return [self.mapper.to_domain(db_ws) for db_ws in db_workspaces]
    
    async def delete(self, workspace_id: str) -> bool:
        """Delete workspace"""
        result = await self.session.execute(
            select(DBWorkspace).where(DBWorkspace.id == workspace_id)
        )
        db_workspace = result.scalar_one_or_none()
        
        if not db_workspace:
            return False
        
        await self.session.delete(db_workspace)
        await self.session.flush()
        
        return True

