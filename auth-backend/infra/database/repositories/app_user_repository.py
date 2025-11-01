"""
App User Repository Implementation
Concrete implementation using PostgreSQL + SQLAlchemy
Adapted for multi-tenant architecture with client_id filtering
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, delete as sql_delete, and_, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from core.interfaces.secondary.app_user_repository_interface import (
    AppUserRepositoryInterface,
)
from core.domain.auth.app_user import AppUser
from core.services.filters.user_filter import UserFilter
from infra.database.models.app_user import DBAppUser
from infra.database.mappers.app_user_mapper import AppUserMapper
from core.exceptions import (
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    IntegrityException,
)
import logging

logger = logging.getLogger(__name__)


class AppUserRepository(IAppUserRepository):
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
        """
        Lists all users with optional filtering, pagination, and sorting.
        
        Filter Pattern: Applies all filters, pagination, and sorting at SQL level.
        
        Returns:
            List of users (empty list if error, graceful degradation)
        """
        try:
            query = select(DBAppUser)
            conditions = []
            
            if filter:
                # Multi-tenant: Always filter by client_id if provided
                if filter.client_id:
                    conditions.append(DBAppUser.client_id == filter.client_id)
                
                # Apply search filter (from BaseFilter)
                if filter.search:
                    search_conditions = [
                        DBAppUser.username.ilike(f"%{filter.search}%"),
                        DBAppUser.email.ilike(f"%{filter.search}%"),
                        DBAppUser.full_name.ilike(f"%{filter.search}%"),
                    ]
                    conditions.append(or_(*search_conditions))
                
                # Apply specific filters
                if filter.email:
                    conditions.append(DBAppUser.email.ilike(f"%{filter.email}%"))
                if filter.username:
                    conditions.append(DBAppUser.username.ilike(f"%{filter.username}%"))
                if filter.role:
                    conditions.append(DBAppUser.role == filter.role.value)
                if filter.active is not None:
                    conditions.append(DBAppUser.is_active == filter.active)
                
                # Add all conditions
                if conditions:
                    query = query.where(and_(*conditions))
                
                # Apply sorting (from BaseFilter)
                if filter.sort_by:
                    column = getattr(DBAppUser, filter.sort_by, None)
                    if column is not None:
                        if filter.sort_order == "desc":
                            query = query.order_by(column.desc())
                        else:
                            query = query.order_by(column.asc())
                else:
                    # Default ordering
                    query = query.order_by(DBAppUser.full_name)
                
                # Apply pagination (from BaseFilter)
                if filter.limit is not None or filter.page_size is not None:
                    query = query.limit(filter.get_limit())
                if filter.offset is not None or filter.page is not None:
                    query = query.offset(filter.get_offset())
            else:
                # No filter - apply default ordering
                query = query.order_by(DBAppUser.full_name)
            
            result = await self.session.execute(query)
            db_users = result.scalars().all()
            return [AppUserMapper.to_domain(u) for u in db_users]
            
        except DatabaseError as e:
            logger.error(f"Database error listing users: {e}", exc_info=True)
            # Graceful degradation: return empty list
            return []
        except Exception as e:
            logger.error(f"Error listing users: {e}", exc_info=True)
            # Graceful degradation: return empty list
            return []
    
    async def find_by_id(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Finds by ID with optional client_id filtering (multi-tenant).
        
        Returns None if not found (NOT an exception).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for multi-tenant isolation
        """
        try:
            query = select(DBAppUser).where(DBAppUser.id == user_id)
            
            # Multi-tenant: Filter by client_id if provided
            if client_id:
                query = query.where(DBAppUser.client_id == client_id)
            
            result = await self.session.execute(query)
            db_user = result.scalar_one_or_none()
            
            if db_user:
                return AppUserMapper.to_domain(db_user)
            
            return None
            
        except DatabaseError as e:
            logger.error(f"Database error finding user {user_id}: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error finding user {user_id}: {e}", exc_info=True)
            raise DomainException("Failed to find user", "REPOSITORY_ERROR")
    
    async def find_by_ids(self, user_ids: List[str], client_id: Optional[str] = None) -> List[AppUser]:
        """
        Finds multiple users by their IDs (batch operation).
        
        Optimized for batch requests - single query instead of N queries.
        Prevents N+1 query problems when fetching multiple users.
        
        Args:
            user_ids: List of user IDs
            client_id: Optional client ID for multi-tenant isolation
            
        Returns:
            List of users found (may be less than requested if some don't exist)
        """
        try:
            if not user_ids:
                return []
            
            query = select(DBAppUser).where(DBAppUser.id.in_(user_ids))
            
            # Multi-tenant: Filter by client_id if provided
            if client_id:
                query = query.where(DBAppUser.client_id == client_id)
            
            result = await self.session.execute(query)
            db_users = result.scalars().all()
            
            return [AppUserMapper.to_domain(db_user) for db_user in db_users]
        
        except DatabaseError as e:
            logger.error(f"Database error finding users by IDs: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error finding users by IDs: {e}", exc_info=True)
            raise DomainException("Failed to find users", "REPOSITORY_ERROR")
    
    async def find_by_email(self, email: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Finds by email with optional client_id filtering (multi-tenant).
        
        Returns None if not found (NOT an exception).
        
        Args:
            email: User email
            client_id: Optional client ID for multi-tenant isolation
        """
        try:
            query = select(DBAppUser).where(DBAppUser.email == email)
            
            # Multi-tenant: Filter by client_id if provided
            # Note: In multi-tenant, email should be unique per client, not globally
            if client_id:
                query = query.where(DBAppUser.client_id == client_id)
            
            result = await self.session.execute(query)
            db_user = result.scalar_one_or_none()
            
            if db_user:
                return AppUserMapper.to_domain(db_user)
            
            return None
            
        except DatabaseError as e:
            logger.error(f"Database error finding user by email {email}: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}", exc_info=True)
            raise DomainException("Failed to find user", "REPOSITORY_ERROR")
    
    async def save(self, user: AppUser) -> AppUser:
        """
        Save user with error handling.
        
        Translates database errors to domain exceptions.
        
        Raises:
            EntityNotFoundException: If trying to update non-existent user
            DuplicateEntityException: If unique constraint violation (email, username)
            DomainException: If other database error occurs
        """
        try:
            if user.id:
                # Update existing
                query = select(DBAppUser).where(DBAppUser.id == user.id)
                result = await self.session.execute(query)
                db_user = result.scalar_one_or_none()
                
                if not db_user:
                    raise EntityNotFoundException("User", user.id)
                
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
            
        except EntityNotFoundException:
            # Expected domain exception - let it propagate
            raise
        except IntegrityError as e:
            # Database constraint violation (unique, foreign key, etc.)
            logger.warning(f"Integrity error saving user: {e}")
            
            # Parse error to provide meaningful message
            error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
            
            if 'unique' in error_str:
                if 'email' in error_str:
                    # Unique constraint on email
                    raise DuplicateEntityException("User", "email", user.email)
                elif 'username' in error_str:
                    # Unique constraint on username
                    raise DuplicateEntityException("User", "username", user.username)
                else:
                    # Other unique constraint
                    raise DuplicateEntityException("User", "unknown", "value")
            elif 'foreign key' in error_str:
                # Foreign key violation
                raise DomainException(
                    "Cannot save user due to referential integrity",
                    "REFERENTIAL_INTEGRITY_ERROR"
                )
            else:
                # Other integrity error
                raise DomainException(
                    "Cannot save user due to data integrity rules",
                    "DATA_INTEGRITY_ERROR"
                )
        except DatabaseError as e:
            # Database connection or query error
            logger.error(f"Database error saving user: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except SQLAlchemyError as e:
            # Other SQLAlchemy errors
            logger.error(f"SQLAlchemy error saving user: {e}", exc_info=True)
            raise DomainException("Failed to save user", "REPOSITORY_ERROR")
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error saving user: {e}", exc_info=True)
            raise DomainException("Unexpected error saving user", "UNEXPECTED_REPOSITORY_ERROR")
    
    async def delete(self, user_id: str, client_id: Optional[str] = None) -> bool:
        """
        Delete user with error handling.
        
        Args:
            user_id: User ID
            client_id: Optional client ID for validation
            
        Raises:
            IntegrityException: If user has related records (foreign key constraint)
            DomainException: If other database error occurs
        """
        try:
            query = sql_delete(DBAppUser).where(DBAppUser.id == user_id)
            
            # Multi-tenant: Add client_id filter if provided
            if client_id:
                query = query.where(DBAppUser.client_id == client_id)
            
            result = await self.session.execute(query)
            await self.session.flush()
            
            return result.rowcount > 0
            
        except IntegrityError as e:
            # Foreign key constraint (user has related records)
            logger.warning(f"Cannot delete user {user_id} - has related records: {e}")
            raise IntegrityException(
                "User",
                user_id,
                dependent_entities=["related records"]
            )
        except DatabaseError as e:
            logger.error(f"Database error deleting user {user_id}: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
            raise DomainException("Failed to delete user", "REPOSITORY_ERROR")
    
    async def count(self, filter: Optional[UserFilter] = None) -> int:
        """
        Counts users with optional filtering.
        
        Filter Pattern: Uses same filter conditions as find_all() but WITHOUT pagination/sorting.
        Essential for calculating total_pages in paginated responses.
        
        Returns:
            Count (0 if error, graceful degradation)
        """
        try:
            query = select(func.count(DBAppUser.id))
            
            if filter:
                conditions = []
                
                # Multi-tenant: Always filter by client_id if provided
                if filter.client_id:
                    conditions.append(DBAppUser.client_id == filter.client_id)
                
                # Apply search filter (from BaseFilter)
                if filter.search:
                    search_conditions = [
                        DBAppUser.username.ilike(f"%{filter.search}%"),
                        DBAppUser.email.ilike(f"%{filter.search}%"),
                        DBAppUser.full_name.ilike(f"%{filter.search}%"),
                    ]
                    conditions.append(or_(*search_conditions))
                
                # Apply specific filters (same as find_all)
                if filter.email:
                    conditions.append(DBAppUser.email.ilike(f"%{filter.email}%"))
                if filter.username:
                    conditions.append(DBAppUser.username.ilike(f"%{filter.username}%"))
                if filter.role:
                    conditions.append(DBAppUser.role == filter.role.value)
                if filter.active is not None:
                    conditions.append(DBAppUser.is_active == filter.active)
                
                # Add all conditions (NO pagination or sorting)
                if conditions:
                    query = query.where(and_(*conditions))
            
            result = await self.session.execute(query)
            return result.scalar() or 0
            
        except DatabaseError as e:
            logger.error(f"Database error counting users: {e}", exc_info=True)
            # Graceful degradation: return 0
            return 0
        except Exception as e:
            logger.error(f"Error counting users: {e}", exc_info=True)
            # Graceful degradation: return 0
            return 0

