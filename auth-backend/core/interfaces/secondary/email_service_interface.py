"""
Email Service Interface
Defines contract for email sending operations (Dependency Inversion Principle)
"""
from abc import ABC, abstractmethod
from typing import Optional


class EmailServiceInterface(ABC):
    """
    Email service interface - defines email sending contract.
    
    Following:
    - Dependency Inversion Principle (depend on abstraction)
    - Interface Segregation Principle (focused interface)
    """
    
    @abstractmethod
    async def send_password_reset_email(self, email: str, reset_token: str, client_id: str) -> bool:
        """
        Send password reset email with reset token link.
        
        Args:
            email: Recipient email address
            reset_token: Password reset token
            client_id: Client (tenant) ID for multi-tenant context
            
        Returns:
            True if email sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send generic email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        pass

