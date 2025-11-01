"""
Email Service Interface
Defines contract for email sending operations (Dependency Inversion Principle)
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class EmailAttachment:
    """Email attachment data."""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Complete email message data."""
    # Required
    to: List[str]
    subject: str
    
    # Content (at least one required)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    
    # Optional recipients
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    
    # Attachments
    attachments: Optional[List[EmailAttachment]] = None
    
    # Headers
    headers: Optional[Dict[str, str]] = None
    
    # Priority
    priority: EmailPriority = EmailPriority.NORMAL
    
    # Tracking
    track_opens: bool = False
    track_clicks: bool = False
    
    # Tags for analytics
    tags: Optional[List[str]] = None
    
    # Scheduling
    send_at: Optional[datetime] = None


class IEmailService(ABC):
    """
    Email service interface - defines email sending contract.
    
    Following:
    - Dependency Inversion Principle (depend on abstraction)
    - Interface Segregation Principle (focused interface)
    """
    
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> Dict:
        """
        Send an email.
        
        Args:
            message: EmailMessage with all email data
            
        Returns:
            Dict with status and message_id:
            {
                "success": bool,
                "message_id": str,
                "status": str,
                "error": str (if failed)
            }
        """
        pass
    
    @abstractmethod
    async def send_template_email(
        self,
        to: List[str],
        subject: str,
        template_name: str,
        context: dict,
        **kwargs
    ) -> Dict:
        """
        Send email using a template.
        
        Args:
            to: Recipient email addresses
            subject: Email subject
            template_name: Template file name (without .html)
            context: Template variables
            **kwargs: Additional EmailMessage fields
            
        Returns:
            Dict with status and message_id
        """
        pass
    
    @abstractmethod
    async def send_bulk_email(
        self,
        messages: List[EmailMessage]
    ) -> List[Dict]:
        """
        Send multiple emails in batch.
        
        Args:
            messages: List of email messages
            
        Returns:
            List of results for each email
        """
        pass
    
    @abstractmethod
    async def validate_email(self, email: str) -> bool:
        """
        Validate email address format and domain.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_email_status(self, message_id: str) -> Dict:
        """
        Get delivery status of sent email.
        
        Args:
            message_id: Email message ID
            
        Returns:
            Dict with status information
        """
        pass
    
    # Legacy methods for backward compatibility
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

