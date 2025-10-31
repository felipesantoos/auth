"""
Password Reset Service Interface
Defines password reset operations (forgot password, reset password)
Following Interface Segregation Principle
"""
from abc import ABC, abstractmethod


class IPasswordResetService(ABC):
    """
    Password reset operations interface.
    
    Following Interface Segregation Principle - clients that only need password reset
    don't need to depend on full authentication operations.
    """
    
    @abstractmethod
    async def forgot_password(self, email: str, client_id: str) -> bool:
        """
        Request password reset (generate reset token).
        
        Generates a password reset token, stores it in Redis, and sends email to user.
        
        Args:
            email: User email address
            client_id: Client (tenant) ID for multi-tenant isolation
            
        Returns:
            True if successful (always returns True for security - don't reveal if email exists)
            
        Raises:
            ValueError: If email doesn't exist for the given client
        """
        pass
    
    @abstractmethod
    async def reset_password(self, reset_token: str, new_password: str, client_id: str) -> bool:
        """
        Reset password using reset token.
        
        Args:
            reset_token: Password reset token from forgot_password
            new_password: New password to set
            client_id: Client (tenant) ID for validation
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If reset token is invalid, expired, or already used
        """
        pass

