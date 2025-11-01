"""
Permission Repository
Data access layer for permissions
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.interfaces.secondary.permission_repository_interface import IPermissionRepository
from core.domain.auth.permission import Permission
from infra.database.models.permission import PermissionModel
from infra.database.mappers.permission_mapper import PermissionMapper


class PermissionRepository(IPermissionRepository):
    """Repository implementation for permissions"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, permission: Permission) -> Permission:
        """Save permission to database"""
        model = PermissionMapper.to_model(permission)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return PermissionMapper.to_domain(model)
    
    async def find_by_id(self, permission_id: str) -> Optional[Permission]:
        """Find permission by ID"""
        result = await self.session.execute(
            select(PermissionModel).where(PermissionModel.id == permission_id)
        )
        model = result.scalar_one_or_none()
        return PermissionMapper.to_domain(model) if model else None
    
    async def find_by_user(self, user_id: str, client_id: str) -> List[Permission]:
        """Find all permissions for user"""
        result = await self.session.execute(
            select(PermissionModel).where(
                PermissionModel.user_id == user_id,
                PermissionModel.client_id == client_id
            )
        )
        models = result.scalars().all()
        return [PermissionMapper.to_domain(m) for m in models]
    
    async def find_by_user_and_resource_type(
        self, user_id: str, client_id: str, resource_type: str  # String livre! ✨
    ) -> List[Permission]:
        """Find permissions for user and specific resource type"""
        result = await self.session.execute(
            select(PermissionModel).where(
                PermissionModel.user_id == user_id,
                PermissionModel.client_id == client_id,
                PermissionModel.resource_type == resource_type.lower().strip()  # Normalizar
            )
        )
        models = result.scalars().all()
        return [PermissionMapper.to_domain(m) for m in models]
    
    async def delete(self, permission_id: str) -> bool:
        """Delete permission"""
        result = await self.session.execute(
            select(PermissionModel).where(PermissionModel.id == permission_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False

