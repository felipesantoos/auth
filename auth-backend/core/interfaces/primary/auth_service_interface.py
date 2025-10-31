"""
Auth Service Interface
Defines core authentication operations (login, logout, register, etc.)
Following Interface Segregation Principle
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from core.domain.auth.app_user import AppUser
from core.services.filters.user_filter import UserFilter


class IAuthService(ABC):
    """
    Core authentication operations interface.
    
    Following Interface Segregation Principle - focused on core auth operations.
    Clients that only need login/logout don't need password reset or OAuth methods.
    """
    
    @abstractmethod
    async def login(self, email: str, password: str, client_id: str) -> Tuple[str, str, AppUser]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: Plain text password
            client_id: Client (tenant) ID for multi-tenant isolation
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            ValueError: If credentials are invalid or user doesn't belong to client
        """
        pass
    
    @abstractmethod
    async def logout(self, refresh_token: str, client_id: Optional[str] = None) -> bool:
        """
        Logout user by invalidating refresh token.
        
        Args:
            refresh_token: Refresh token to invalidate
            client_id: Optional client ID for validation
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str, client_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            client_id: Optional client ID for validation
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            ValueError: If refresh token is invalid
        """
        pass
    
    @abstractmethod
    async def register(self, username: str, email: str, password: str, name: str, client_id: str) -> AppUser:
        """
        Register new user.
        
        Args:
            username: Unique username
            email: User email
            password: Plain text password
            name: User full name
            client_id: Client (tenant) ID
            
        Returns:
            Created user
            
        Raises:
            ValueError: If email already exists or validation fails
        """
        pass
    
    @abstractmethod
    async def change_password(
        self, user_id: str, old_password: str, new_password: str, client_id: Optional[str] = None
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            client_id: Optional client ID for validation
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If old password is incorrect
        """
        pass
    
    @abstractmethod
    async def get_current_user(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get current user by ID.
        
        Args:
            user_id: User ID from JWT token
            client_id: Optional client ID for validation
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload if valid, None otherwise
        """
        pass
    
    # ========== Admin Operations ==========
    
    @abstractmethod
    async def list_all_users(self, filter: Optional[UserFilter] = None) -> List[AppUser]:
        """
        List all users with optional filter (admin only).
        
        Filter Pattern: Service accepts filter and passes directly to repository.
        No conditional logic here - repository handles all filtering, pagination, and sorting.
        
        Args:
            filter: Optional filter object containing:
                - search: General search term (BaseFilter) - searches in username, email, name
                - page/page_size or offset/limit: Pagination (BaseFilter)
                - sort_by/sort_order: Sorting (BaseFilter)
                - client_id: Filter by client (tenant) - required for multi-tenant isolation
                - role, active, email, username: User-specific filters
        
        Returns:
            List of users matching the filter criteria (paginated and sorted)
        """
        pass
    
    @abstractmethod
    async def count_users(self, filter: Optional[UserFilter] = None) -> int:
        """
        Counts users with optional filter.
        
        Filter Pattern: Uses same filter as list_all_users but without pagination/sorting.
        Essential for pagination metadata (total_pages, has_next, etc.).
        
        Args:
            filter: Optional filter object (same filters as list_all_users):
                - search: General search term (BaseFilter)
                - client_id, role, active, email, username: User-specific filters
                - Note: pagination and sorting are ignored in count
        
        Returns:
            Total number of users matching the filter criteria (unpaginated count)
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get user by email (admin only).
        
        Args:
            email: User email
            client_id: Optional client ID for multi-tenant isolation
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get user by ID (admin only).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for multi-tenant isolation
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def admin_update_user(self, user: AppUser) -> AppUser:
        """
        Update user (admin only).
        
        Args:
            user: User domain object with updated fields
            
        Returns:
            Updated user
        """
        pass
    
    @abstractmethod
    async def admin_delete_user(self, user_id: str, admin_id: str, client_id: Optional[str] = None) -> bool:
        """
        Delete user (admin only).
        Prevents self-deletion.
        
        Args:
            user_id: ID of user to delete
            admin_id: ID of admin performing the deletion
            client_id: Optional client ID for validation
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If trying to delete own account
        """
        pass

