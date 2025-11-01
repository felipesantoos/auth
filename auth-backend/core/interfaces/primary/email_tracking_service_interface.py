"""
Email Tracking Service Interface
Primary port for email tracking operations
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime


class IEmailTrackingService(ABC):
    """Interface for email tracking service operations."""
    
    @abstractmethod
    async def track_open(self, message_id: str) -> bool:
        """
        Track email open event.
        
        Args:
            message_id: Email message ID
            
        Returns:
            True if tracked successfully
        """
        pass
    
    @abstractmethod
    async def track_click(
        self,
        message_id: str,
        url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Track email click event.
        
        Args:
            message_id: Email message ID
            url: Clicked URL
            ip_address: User IP address
            user_agent: User agent string
            
        Returns:
            True if tracked successfully
        """
        pass
    
    @abstractmethod
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_name: Optional[str] = None
    ) -> Dict:
        """
        Get email analytics metrics.
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            template_name: Filter by template name
            
        Returns:
            Analytics metrics dictionary
        """
        pass
    
    @abstractmethod
    async def get_preferences(self, token: str) -> Optional[Dict]:
        """
        Get email subscription preferences.
        
        Args:
            token: Unsubscribe token
            
        Returns:
            Preferences dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def update_preferences(
        self,
        token: str,
        marketing: Optional[bool] = None,
        notifications: Optional[bool] = None,
        updates: Optional[bool] = None,
        newsletter: Optional[bool] = None
    ) -> Optional[Dict]:
        """
        Update email subscription preferences.
        
        Args:
            token: Unsubscribe token
            marketing: Marketing emails preference
            notifications: Notification emails preference
            updates: Product updates preference
            newsletter: Newsletter preference
            
        Returns:
            Updated preferences or None if not found
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, token: str, reason: str = "user_request") -> bool:
        """
        Unsubscribe user from all emails.
        
        Args:
            token: Unsubscribe token
            reason: Unsubscribe reason
            
        Returns:
            True if unsubscribed successfully
        """
        pass

