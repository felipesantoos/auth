"""
Email Webhook Service Interface
Primary port for handling email provider webhooks
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class IEmailWebhookService(ABC):
    """
    Interface for email webhook service operations.
    
    Handles webhooks from email providers (SendGrid, AWS SES, Mailgun)
    for bounces, spam complaints, deliveries, etc.
    """
    
    @abstractmethod
    async def handle_bounce(
        self,
        email: str,
        message_id: Optional[str] = None,
        bounce_type: str = "hard",
        bounce_reason: Optional[str] = None
    ) -> bool:
        """
        Handle email bounce event.
        
        Args:
            email: Email address that bounced
            message_id: Optional message ID
            bounce_type: Type of bounce ('hard' or 'soft')
            bounce_reason: Reason for bounce
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    async def handle_spam_complaint(
        self,
        email: str,
        message_id: Optional[str] = None
    ) -> bool:
        """
        Handle spam complaint event.
        
        User marked email as spam - unsubscribe immediately.
        
        Args:
            email: Email address that complained
            message_id: Optional message ID
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    async def handle_delivery(
        self,
        message_id: str
    ) -> bool:
        """
        Handle successful delivery event.
        
        Args:
            message_id: Message ID that was delivered
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    async def handle_unsubscribe(
        self,
        email: str,
        reason: str = "provider_unsubscribe"
    ) -> bool:
        """
        Handle unsubscribe event from provider.
        
        Args:
            email: Email address to unsubscribe
            reason: Reason for unsubscribe
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    async def handle_open(
        self,
        message_id: str
    ) -> bool:
        """
        Handle email open event from provider webhook.
        
        Args:
            message_id: Message ID that was opened
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    async def handle_click(
        self,
        message_id: str,
        url: Optional[str] = None
    ) -> bool:
        """
        Handle email click event from provider webhook.
        
        Args:
            message_id: Message ID where link was clicked
            url: Optional URL that was clicked
            
        Returns:
            True if handled successfully
        """
        pass
    
    @abstractmethod
    async def process_sendgrid_event(self, event: Dict) -> bool:
        """
        Process SendGrid-specific webhook event.
        
        Args:
            event: SendGrid event data
            
        Returns:
            True if processed successfully
        """
        pass
    
    @abstractmethod
    async def process_ses_event(self, message: Dict) -> bool:
        """
        Process AWS SES SNS notification event.
        
        Args:
            message: SES message data
            
        Returns:
            True if processed successfully
        """
        pass

