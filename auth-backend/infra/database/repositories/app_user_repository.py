"""
App User Repository Implementation
Concrete implementation using PostgreSQL + SQLAlchemy
Adapted for multi-tenant architecture with client_id filtering
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, delete as sql_delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from core.interfaces.secondary.app_user_repository_interface import (
    AppUserRepositoryInterface,
)
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_filter import UserFilter
from infra.database.models.app_user import DBAppUser
from infra.database.mappers.app_user_mapper import AppUserMapper


class AppUserRepository(AppUserRepositoryInterface):
    """
    PostgreSQL repository implementation.
    
    Adapter that implements the repository interface.
    Domain doesn't depend on this - only on the interface.
    
    Multi-tenant: All queries respect client_id isolation.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Constructor injection.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def find_all(self, filter: Optional[UserFilter] = None) -> List[AppUser]:
        """Lists all users with optional filtering (respects client_id)"""
        query = select(DBAppUser)
        conditions = []
        
        # Multi-tenant: Always filter by client_id if provided
        if filter and filter.client_id:
            conditions.append(DBAppUser.client_id == filter.client_id)
        
        if filter:
            # Apply specific filters
            if filter.email:
                conditions.append(DBAppUser.email.ilike(f"%{filter.email}%"))
            if filter.username:
                conditions.append(DBAppUser.username.ilike(f"%{filter.username}%"))
            if filter.role:
                conditions.append(DBAppUser.role == filter.role.value)
            if filter.active is not None:
                conditions.append(DBAppUser.is_active == filter.active)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Default ordering
        query = query.order_by(DBAppUser.full_name)
        
        result = await self.session.execute(query)
        db_users = result.scalars().all()
        return [AppUserMapper.to_domain(u) for u in db_users]
    
    async def find_by_id(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Finds by ID with optional client_id filtering (multi-tenant).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for multi-tenant isolation
        """
        query = select(DBAppUser).where(DBAppUser.id == user_id)
        
        # Multi-tenant: Filter by client_id if provided
        if client_id:
            query = query.where(DBAppUser.client_id == client_id)
        
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        return AppUserMapper.to_domain(db_user) if db_user else None
    
    async def find_by_email(self, email: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Finds by email with optional client_id filtering (multi-tenant).
        
        Args:
            email: User email
            client_id: Optional client ID for multi-tenant isolation
        """
        query = select(DBAppUser).where(DBAppUser.email == email)
        
        # Multi-tenant: Filter by client_id if provided
        # Note: In multi-tenant, email should be unique per client, not globally
        if client_id:
            query = query.where(DBAppUser.client_id == client_id)
        
        result = await self.session.execute(query)
        db_user = result.scalar_one_or_none()
        return AppUserMapper.to_domain(db_user) if db_user else None
    
    async def save(self, user: AppUser) -> AppUser:
        """Saves or updates"""
        if user.id:
            # Update existing
            query = select(DBAppUser).where(DBAppUser.id == user.id)
            result = await self.session.execute(query)
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                raise ValueError(f"User with id {user.id} not found")
            
            db_user.username = user.username
            db_user.email = user.email
            db_user.hashed_password = user.password_hash
            db_user.full_name = user.name
            db_user.role = user.role.value
            db_user.is_active = user.active
            db_user.client_id = user.client_id  # Multi-tenant
            db_user.updated_at = datetime.utcnow()
        else:
            # Create new
            db_user = DBAppUser(
                username=user.username,
                email=user.email,
                hashed_password=user.password_hash,
                full_name=user.name,
                role=user.role.value,
                is_active=user.active,
                client_id=user.client_id,  # Multi-tenant
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.session.add(db_user)
        
        await self.session.flush()
        await self.session.refresh(db_user)
        return AppUserMapper.to_domain(db_user)
    
    async def delete(self, user_id: str, client_id: Optional[str] = None) -> bool:
        """
        Deletes user with optional client_id validation (multi-tenant).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for validation
        """
        query = sql_delete(DBAppUser).where(DBAppUser.id == user_id)
        
        # Multi-tenant: Add client_id filter if provided
        if client_id:
            query = query.where(DBAppUser.client_id == client_id)
        
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount > 0

