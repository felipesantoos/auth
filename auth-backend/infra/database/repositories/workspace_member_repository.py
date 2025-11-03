"""Workspace Member Repository Implementation"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from core.domain.workspace.workspace_member import WorkspaceMember
from core.interfaces.secondary.workspace_member_repository import IWorkspaceMemberRepository
from infra.database.models.workspace_member import DBWorkspaceMember
from infra.database.mappers.workspace_member_mapper import WorkspaceMemberMapper
from core.exceptions import DuplicateEntityException, NotFoundException


class WorkspaceMemberRepository(IWorkspaceMemberRepository):
    """PostgreSQL implementation of workspace member repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = WorkspaceMemberMapper()
    
    async def save(self, member: WorkspaceMember) -> WorkspaceMember:
        """Save or update workspace member"""
        try:
            if member.id:
                # Update existing
                result = await self.session.execute(
                    select(DBWorkspaceMember).where(DBWorkspaceMember.id == member.id)
                )
                db_member = result.scalar_one_or_none()
                
                if not db_member:
                    raise NotFoundException(f"Workspace member not found: {member.id}")
                
                db_member = self.mapper.update_db_from_domain(db_member, member)
            else:
                # Create new
                db_member = self.mapper.to_db(member)
                self.session.add(db_member)
            
            await self.session.flush()
            await self.session.refresh(db_member)
            
            return self.mapper.to_domain(db_member)
            
        except IntegrityError as e:
            await self.session.rollback()
            if 'uq_user_workspace' in str(e):
                raise DuplicateEntityException(
                    f"User {member.user_id} is already a member of workspace {member.workspace_id}"
                )
            raise
    
    async def find_by_id(self, member_id: str) -> Optional[WorkspaceMember]:
        """Find workspace member by ID"""
        result = await self.session.execute(
            select(DBWorkspaceMember).where(DBWorkspaceMember.id == member_id)
        )
        db_member = result.scalar_one_or_none()
        
        return self.mapper.to_domain(db_member) if db_member else None
    
    async def find_by_user_and_workspace(
        self, user_id: str, workspace_id: str
    ) -> Optional[WorkspaceMember]:
        """Find workspace member by user and workspace"""
        result = await self.session.execute(
            select(DBWorkspaceMember).where(
                DBWorkspaceMember.user_id == user_id,
                DBWorkspaceMember.workspace_id == workspace_id
            )
        )
        db_member = result.scalar_one_or_none()
        
        return self.mapper.to_domain(db_member) if db_member else None
    
    async def find_by_user(self, user_id: str, active_only: bool = True) -> List[WorkspaceMember]:
        """Find all workspaces for a user"""
        query = select(DBWorkspaceMember).where(DBWorkspaceMember.user_id == user_id)
        
        if active_only:
            query = query.where(DBWorkspaceMember.active == True)
        
        result = await self.session.execute(query.order_by(DBWorkspaceMember.created_at.desc()))
        db_members = result.scalars().all()
        
        return [self.mapper.to_domain(db_m) for db_m in db_members]
    
    async def find_by_workspace(
        self, workspace_id: str, active_only: bool = True
    ) -> List[WorkspaceMember]:
        """Find all members of a workspace"""
        query = select(DBWorkspaceMember).where(DBWorkspaceMember.workspace_id == workspace_id)
        
        if active_only:
            query = query.where(DBWorkspaceMember.active == True)
        
        result = await self.session.execute(query.order_by(DBWorkspaceMember.created_at.desc()))
        db_members = result.scalars().all()
        
        return [self.mapper.to_domain(db_m) for db_m in db_members]
    
    async def delete(self, member_id: str) -> bool:
        """Delete workspace member"""
        result = await self.session.execute(
            select(DBWorkspaceMember).where(DBWorkspaceMember.id == member_id)
        )
        db_member = result.scalar_one_or_none()
        
        if not db_member:
            return False
        
        await self.session.delete(db_member)
        await self.session.flush()
        
        return True

