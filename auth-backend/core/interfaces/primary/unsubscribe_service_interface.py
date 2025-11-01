"""
Unsubscribe Service Interface
Primary port for email subscription management
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict


class IUnsubscribeService(ABC):
    """Interface for email subscription and unsubscribe operations."""
    
    @abstractmethod
    def create_unsubscribe_token(self, email: str) -> str:
        """
        Generate secure unsubscribe token.
        
        Args:
            email: Email address
            
        Returns:
            Secure token string
        """
        pass
    
    @abstractmethod
    async def create_subscription(
        self,
        email: str,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Create email subscription with unsubscribe token.
        
        Args:
            email: Email address
            user_id: Optional user ID
            
        Returns:
            Subscription data with token
        """
        pass
    
    @abstractmethod
    async def unsubscribe(
        self,
        email: Optional[str] = None,
        token: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Unsubscribe user from all emails.
        
        Args:
            email: Email address (if known)
            token: Unsubscribe token
            reason: Reason for unsubscribing
            
        Returns:
            True if unsubscribed successfully
        """
        pass
    
    @abstractmethod
    async def update_preferences(
        self,
        email: str,
        marketing_emails: Optional[bool] = None,
        notification_emails: Optional[bool] = None,
        product_updates: Optional[bool] = None,
        newsletter: Optional[bool] = None
    ) -> bool:
        """
        Update granular email preferences.
        
        Args:
            email: Email address
            marketing_emails: Receive marketing emails
            notification_emails: Receive notification emails
            product_updates: Receive product updates
            newsletter: Receive newsletter
            
        Returns:
            True if updated successfully
        """
        pass
    
    @abstractmethod
    async def can_send_email(self, email: str, email_type: str) -> bool:
        """
        Check if user can receive this type of email.
        
        Args:
            email: Email address
            email_type: Type of email (transactional, marketing, notification, etc)
            
        Returns:
            True if email can be sent
        """
        pass
    
    @abstractmethod
    async def get_preferences(self, email: str) -> Optional[dict]:
        """
        Get email preferences for a user.
        
        Args:
            email: Email address
            
        Returns:
            Dict with preferences or None
        """
        pass

