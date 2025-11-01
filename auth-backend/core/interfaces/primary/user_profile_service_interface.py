"""
User Profile Service Interface
Port for user profile management operations
"""
from abc import ABC, abstractmethod
from typing import Optional
from core.domain.auth.app_user import AppUser


class IUserProfileService(ABC):
    """Interface for user profile service operations"""
    
    @abstractmethod
    async def update_profile(
        self,
        user_id: str,
        client_id: str,
        name: Optional[str] = None,
        username: Optional[str] = None
    ) -> AppUser:
        """Update user profile"""
        pass
    
    @abstractmethod
    async def request_email_change(
        self,
        user_id: str,
        new_email: str,
        password: str
    ) -> str:
        """Request email change"""
        pass
    
    @abstractmethod
    async def delete_account(
        self,
        user_id: str,
        password: str
    ) -> bool:
        """Delete account (soft delete)"""
        pass

