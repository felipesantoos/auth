"""
OAuth Service Interface
Defines OAuth2 authentication operations
Following Interface Segregation Principle
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from core.domain.auth.app_user import AppUser


class IOAuthService(ABC):
    """
    OAuth2 operations interface.
    
    Following Interface Segregation Principle - clients that only need OAuth
    don't need to depend on password-based authentication operations.
    """
    
    @abstractmethod
    async def oauth_login(
        self,
        provider: str,
        email: str,
        name: str,
        oauth_id: Optional[str] = None,
        client_id: str = None
    ) -> Tuple[str, str, AppUser]:
        """
        Login or register user via OAuth2 (multi-tenant).
        
        Creates user if doesn't exist, or logs in existing user.
        
        Args:
            provider: OAuth provider name (e.g., 'google', 'github')
            email: User email from OAuth provider
            name: User name from OAuth provider
            oauth_id: Optional OAuth provider user ID
            client_id: Client (tenant) ID for multi-tenant isolation
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            ValueError: If client_id is invalid or user creation fails
        """
        pass

