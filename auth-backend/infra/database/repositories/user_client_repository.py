"""User Client Repository Implementation"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from core.interfaces.secondary.user_client_repository import IUserClientRepository
from infra.database.models.user_client import DBUserClient
from core.exceptions import DuplicateEntityException


class UserClientRepository(IUserClientRepository):
    """PostgreSQL implementation of user-client repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, user_client: DBUserClient) -> DBUserClient:
        """Save or update user-client access"""
        try:
            if user_client.id:
                # Already has ID, merge
                user_client = await self.session.merge(user_client)
            else:
                # New record
                self.session.add(user_client)
            
            await self.session.flush()
            await self.session.refresh(user_client)
            
            return user_client
            
        except IntegrityError as e:
            await self.session.rollback()
            if 'uq_user_client' in str(e):
                raise DuplicateEntityException(
                    f"User {user_client.user_id} already has access to client {user_client.client_id}"
                )
            raise
    
    async def find_by_user_and_client(
        self, user_id: str, client_id: str
    ) -> Optional[DBUserClient]:
        """Find user-client access by user and client"""
        result = await self.session.execute(
            select(DBUserClient).where(
                and_(
                    DBUserClient.user_id == user_id,
                    DBUserClient.client_id == client_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def find_by_user(self, user_id: str, active_only: bool = True) -> List[DBUserClient]:
        """Find all client accesses for a user"""
        query = select(DBUserClient).where(DBUserClient.user_id == user_id)
        
        if active_only:
            query = query.where(DBUserClient.active == True)
        
        result = await self.session.execute(query.order_by(DBUserClient.granted_at.desc()))
        return list(result.scalars().all())
    
    async def find_by_client(self, client_id: str, active_only: bool = True) -> List[DBUserClient]:
        """Find all user accesses for a client"""
        query = select(DBUserClient).where(DBUserClient.client_id == client_id)
        
        if active_only:
            query = query.where(DBUserClient.active == True)
        
        result = await self.session.execute(query.order_by(DBUserClient.granted_at.desc()))
        return list(result.scalars().all())
    
    async def delete(self, user_id: str, client_id: str) -> bool:
        """Delete user-client access"""
        result = await self.session.execute(
            select(DBUserClient).where(
                and_(
                    DBUserClient.user_id == user_id,
                    DBUserClient.client_id == client_id
                )
            )
        )
        user_client = result.scalar_one_or_none()
        
        if not user_client:
            return False
        
        await self.session.delete(user_client)
        await self.session.flush()
        
        return True

