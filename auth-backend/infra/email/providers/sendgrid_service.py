"""
SendGrid Email Service Provider
Optional provider for SendGrid API
"""
import logging
from typing import List, Dict

from core.interfaces.secondary.email_service_interface import (
    IEmailService,
    EmailMessage
)
from config.settings import settings

logger = logging.getLogger(__name__)


class SendGridEmailService(IEmailService):
    """
    SendGrid email service (recommended for production).
    
    Note: Requires 'sendgrid' package to be installed.
    Install: pip install sendgrid>=6.11.0
    
    Configuration:
    - EMAIL_BACKEND=sendgrid
    - SENDGRID_API_KEY=your_api_key
    """
    
    def __init__(self):
        """Initialize SendGrid service."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            self.SendGridAPIClient = SendGridAPIClient
            self.Mail = Mail
            self.Email = Email
            self.To = To
            self.Content = Content
        except ImportError:
            logger.error("SendGrid package not installed. Install with: pip install sendgrid")
            raise ImportError("SendGrid package required for SendGrid email service")
        
        self.api_key = settings.sendgrid_api_key
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not configured")
        
        self.client = self.SendGridAPIClient(self.api_key)
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        
        logger.info("SendGridEmailService initialized")
    
    async def send_email(self, message: EmailMessage) -> Dict:
        """
        Send email via SendGrid API.
        
        Args:
            message: EmailMessage with all email data
            
        Returns:
            Dict with status and message_id
        """
        try:
            mail = self.Mail()
            mail.from_email = self.Email(self.from_email, self.from_name)
            mail.subject = message.subject
            
            # Add recipients
            for to_email in message.to:
                mail.add_to(self.To(to_email))
            
            # Add content
            if message.html_content:
                mail.add_content(self.Content("text/html", message.html_content))
            if message.text_content:
                mail.add_content(self.Content("text/plain", message.text_content))
            
            # Tracking
            if message.track_opens:
                mail.tracking_settings = {"open_tracking": {"enable": True}}
            if message.track_clicks:
                mail.tracking_settings = {"click_tracking": {"enable": True}}
            
            # Tags for analytics
            if message.tags:
                mail.categories = message.tags
            
            # Send
            response = self.client.send(mail)
            
            return {
                "success": response.status_code == 202,
                "message_id": response.headers.get('X-Message-Id'),
                "status": "accepted"
            }
        
        except Exception as e:
            logger.error(f"SendGrid error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def send_template_email(
        self,
        to: List[str],
        subject: str,
        template_name: str,
        context: dict,
        **kwargs
    ) -> Dict:
        """Send email using a template (not implemented for SendGrid provider)."""
        logger.warning("Template rendering should be done before calling SendGrid provider")
        return {"success": False, "error": "Template rendering not supported by this provider"}
    
    async def send_bulk_email(self, messages: List[EmailMessage]) -> List[Dict]:
        """Send multiple emails in batch."""
        import asyncio
        results = await asyncio.gather(
            *[self.send_email(msg) for msg in messages],
            return_exceptions=True
        )
        return results
    
    async def validate_email(self, email: str) -> bool:
        """Validate email address."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def get_email_status(self, message_id: str) -> Dict:
        """Get delivery status (not implemented)."""
        return {"message_id": message_id, "status": "unknown"}
    
    async def send_password_reset_email(self, email: str, reset_token: str, client_id: str) -> bool:
        """Legacy method (not implemented)."""
        return False

