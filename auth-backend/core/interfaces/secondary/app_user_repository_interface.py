"""
App User Repository Interface
Defines contract for user data persistence (Dependency Inversion Principle)
Adapted for multi-tenant architecture
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.app_user import AppUser
from core.services.filters.user_filter import UserFilter


class IAppUserRepository(ABC):
    """
    Repository interface for AppUser persistence.
    
    Following:
    - Dependency Inversion Principle (depend on abstraction)
    - Interface Segregation Principle (focused interface)
    - Multi-tenant: All queries should respect client_id isolation
    """
    
    @abstractmethod
    async def find_all(self, filter: Optional[UserFilter] = None) -> List[AppUser]:
        """Returns all users matching filter (filtered by client_id if provided)"""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Finds user by ID.
        
        Args:
            user_id: User ID
            client_id: Optional client ID for multi-tenant isolation
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Finds user by email.
        
        Args:
            email: User email
            client_id: Optional client ID for multi-tenant isolation
        """
        pass
    
    @abstractmethod
    async def save(self, user: AppUser) -> AppUser:
        """
        Saves or updates user.
        
        Contract:
        - If user.id is None: Creates new user
        - If user.id is set: Updates existing user
        
        Raises:
            ValueError: If user.id is set but user doesn't exist (attempting to update non-existent user)
            
        Note: This exception is acceptable because it indicates a business logic error
        (trying to update a user that was deleted or never existed). The service layer
        should verify existence before calling save() for updates.
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str, client_id: Optional[str] = None) -> bool:
        """
        Deletes user.
        
        Args:
            user_id: User ID
            client_id: Optional client ID for multi-tenant isolation
        """
        pass
    
    @abstractmethod
    async def count(self, filter: Optional[UserFilter] = None) -> int:
        """
        Counts users with optional filtering.
        
        Filter Pattern: Uses same filter as find_all() but WITHOUT pagination/sorting.
        Essential for calculating total_pages in paginated responses.
        
        Args:
            filter: Optional filter object (applies search and specific filters only):
                - search: General search term (BaseFilter)
                - client_id, role, active, email, username: User-specific filters
                - Note: pagination and sorting are ignored in count
        
        Returns:
            Total number of users matching the filter criteria (unpaginated count)
        """
        pass

