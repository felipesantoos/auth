"""
Email Service Implementation
Production-ready SMTP-based email sending service with comprehensive features
"""
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Dict
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
import re
import dns.resolver
import uuid
import base64

from config.settings import settings
from core.interfaces.secondary.email_service_interface import (
    IEmailService,
    EmailMessage,
    EmailAttachment,
    EmailPriority
)

logger = logging.getLogger(__name__)


class EmailService(IEmailService):
    """
    Production-ready email service with comprehensive features.
    
    Features:
    - Multiple backend support (SMTP, console)
    - Template rendering with Jinja2
    - Inline images and attachments
    - Email validation (format + MX records)
    - Tracking (opens, clicks)
    - CC/BCC support
    - Priority handling
    """
    
    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port or 587
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls
        self.timeout = settings.smtp_timeout
        self.backend = settings.email_backend
        self.tracking_enabled = settings.email_tracking_enabled
        
        # Setup Jinja2 for templates
        template_path = Path(settings.email_templates_dir)
        if template_path.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_path)),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            # Add custom filters
            self.jinja_env.filters['format_currency'] = self._format_currency
            self.jinja_env.filters['format_date'] = self._format_date
        else:
            logger.warning(f"Email templates directory not found: {template_path}")
            self.jinja_env = None
        
        logger.info(f"EmailService initialized (backend: {self.backend})")
    
    def _is_configured(self) -> bool:
        """Check if SMTP is configured."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)
    
    async def send_email(self, message: EmailMessage) -> Dict:
        """
        Send email with full feature support.
        
        Returns:
            {
                "success": bool,
                "message_id": str,
                "status": str,
                "error": str (if failed)
            }
        """
        message_id = str(uuid.uuid4())
        
        try:
            # Validate recipients
            for email in message.to:
                if not await self.validate_email(email):
                    return {
                        "success": False,
                        "message_id": message_id,
                        "status": "invalid_recipient",
                        "error": f"Invalid email: {email}"
                    }
            
            # Build MIME message
            mime_msg = await self._build_mime_message(message, message_id)
            
            # Send based on backend
            if self.backend == "console":
                self._send_to_console(mime_msg)
                status = "sent_to_console"
            elif self._is_configured():
                await self._send_via_smtp(mime_msg, message.to)
                status = "sent"
            else:
                # Fallback to console if not configured
                self._send_to_console(mime_msg)
                status = "sent_to_console"
            
            logger.info(
                f"Email sent successfully",
                extra={
                    "message_id": message_id,
                    "to": message.to,
                    "subject": message.subject
                }
            )
            
            return {
                "success": True,
                "message_id": message_id,
                "status": status
            }
        
        except Exception as e:
            logger.error(
                f"Failed to send email: {e}",
                extra={"message_id": message_id},
                exc_info=True
            )
            return {
                "success": False,
                "message_id": message_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def send_template_email(
        self,
        to: List[str],
        subject: str,
        template_name: str,
        context: dict,
        **kwargs
    ) -> Dict:
        """
        Send email using Jinja2 template.
        
        Args:
            to: Recipient email addresses
            subject: Email subject
            template_name: Template file name (without .html)
            context: Template variables
            **kwargs: Additional EmailMessage fields
        """
        if not self.jinja_env:
            return {
                "success": False,
                "status": "template_error",
                "error": "Template engine not initialized"
            }
        
        try:
            # Add common context variables
            full_context = {
                'app_name': settings.app_name,
                'frontend_url': settings.frontend_url,
                'support_email': settings.smtp_from_email,
                'current_year': datetime.now().year,
                'recipient_email': to[0] if to else '',
                **context
            }
            
            # Render HTML template
            html_template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**full_context)
            
            # Try to render text template (fallback to HTML)
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**full_context)
            except:
                text_content = None
            
            # Create email message
            message = EmailMessage(
                to=to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                **kwargs
            )
            
            return await self.send_email(message)
        
        except Exception as e:
            logger.error(f"Failed to send template email: {e}", exc_info=True)
            return {
                "success": False,
                "status": "template_error",
                "error": str(e)
            }
    
    async def send_bulk_email(
        self,
        messages: List[EmailMessage],
        batch_size: int = 100
    ) -> List[Dict]:
        """
        Send multiple emails in batches.
        
        Args:
            messages: List of email messages
            batch_size: Number of emails to send concurrently
        """
        import asyncio
        
        results = []
        
        # Process in batches
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Send batch concurrently
            batch_results = await asyncio.gather(
                *[self.send_email(msg) for msg in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            
            # Small delay between batches to avoid rate limits
            if i + batch_size < len(messages):
                await asyncio.sleep(1)
        
        return results
    
    async def validate_email(self, email: str) -> bool:
        """
        Validate email address format and domain.
        
        Checks:
        1. Format (regex)
        2. Domain has MX records (if dns available)
        """
        # Format validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Extract domain
        domain = email.split('@')[1]
        
        # Disposable email domains blacklist
        disposable_domains = {
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org'
        }
        
        if domain.lower() in disposable_domains:
            return False
        
        # Check MX records (optional, can be slow)
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(list(mx_records)) > 0
        except:
            # If DNS check fails, accept email (don't block valid emails)
            return True
    
    async def get_email_status(self, message_id: str) -> Dict:
        """Get delivery status from tracking database."""
        # This will be implemented when we have the repository injected
        # For now, return basic status
        return {
            "message_id": message_id,
            "status": "unknown",
            "message": "Tracking not yet implemented in this service layer"
        }
    
    async def _build_mime_message(
        self,
        message: EmailMessage,
        message_id: str
    ) -> MIMEMultipart:
        """Build complete MIME message."""
        # Create multipart message
        mime_msg = MIMEMultipart('mixed')
        
        # Headers
        mime_msg['From'] = f"{self.from_name} <{self.from_email}>"
        mime_msg['To'] = ', '.join(message.to)
        mime_msg['Subject'] = message.subject
        mime_msg['Message-ID'] = f"<{message_id}@{self.from_email.split('@')[1]}>"
        mime_msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        if message.cc:
            mime_msg['Cc'] = ', '.join(message.cc)
        if message.reply_to:
            mime_msg['Reply-To'] = message.reply_to
        
        # Custom headers
        if message.headers:
            for key, value in message.headers.items():
                mime_msg[key] = value
        
        # Priority
        if message.priority == EmailPriority.HIGH:
            mime_msg['X-Priority'] = '1'
            mime_msg['Importance'] = 'high'
        elif message.priority == EmailPriority.LOW:
            mime_msg['X-Priority'] = '5'
            mime_msg['Importance'] = 'low'
        
        # List-Unsubscribe header (important for deliverability)
        unsubscribe_url = f"{settings.frontend_url}/unsubscribe?token={message_id}"
        mime_msg['List-Unsubscribe'] = f"<{unsubscribe_url}>"
        mime_msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
        
        # Create alternative part for text and HTML
        msg_alternative = MIMEMultipart('alternative')
        mime_msg.attach(msg_alternative)
        
        # Add text content
        if message.text_content:
            msg_alternative.attach(MIMEText(message.text_content, 'plain', 'utf-8'))
        
        # Add HTML content with tracking
        html_content = message.html_content or ""
        
        if self.tracking_enabled and message.track_opens:
            # Add tracking pixel
            tracking_url = f"{settings.api_base_url}/api/email/track/open/{message_id}"
            html_content += f'<img src="{tracking_url}" width="1" height="1" alt="" />'
        
        if self.tracking_enabled and message.track_clicks:
            # Replace links with tracking links
            html_content = await self._add_click_tracking(html_content, message_id)
        
        if html_content:
            msg_alternative.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Add attachments
        if message.attachments:
            for attachment in message.attachments:
                self._attach_file(mime_msg, attachment)
        
        return mime_msg
    
    async def _send_via_smtp(
        self,
        mime_msg: MIMEMultipart,
        recipients: List[str]
    ):
        """Send email via SMTP server."""
        smtp = aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=self.use_tls,
            timeout=self.timeout
        )
        
        async with smtp:
            if self.smtp_user and self.smtp_password:
                await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(mime_msg)
        
        logger.debug(f"Email sent via SMTP to {recipients}")
    
    def _send_to_console(self, mime_msg: MIMEMultipart):
        """Print email to console (development)."""
        print("\n" + "="*100)
        print("📧 EMAIL (CONSOLE BACKEND)")
        print("="*100)
        print(f"From: {mime_msg['From']}")
        print(f"To: {mime_msg['To']}")
        if mime_msg.get('Cc'):
            print(f"Cc: {mime_msg['Cc']}")
        print(f"Subject: {mime_msg['Subject']}")
        print(f"Message-ID: {mime_msg['Message-ID']}")
        print("-"*100)
        
        # Print HTML content
        for part in mime_msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode('utf-8')
                # Print first 500 chars
                print(html[:500] + "..." if len(html) > 500 else html)
                break
            elif part.get_content_type() == "text/plain":
                text = part.get_payload(decode=True).decode('utf-8')
                print(text[:500] + "..." if len(text) > 500 else text)
        
        print("="*100 + "\n")
    
    def _attach_file(self, mime_msg: MIMEMultipart, attachment: EmailAttachment):
        """Attach file to email."""
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment.filename}"'
        )
        part.add_header('Content-Type', attachment.content_type)
        mime_msg.attach(part)
    
    async def _add_click_tracking(self, html_content: str, message_id: str) -> str:
        """Replace links with tracking links."""
        def replace_link(match):
            original_url = match.group(1)
            # Don't track unsubscribe links
            if 'unsubscribe' in original_url.lower():
                return f'href="{original_url}"'
            tracking_url = f"{settings.api_base_url}/api/email/track/click/{message_id}?url={original_url}"
            return f'href="{tracking_url}"'
        
        # Replace all href attributes
        return re.sub(r'href="([^"]+)"', replace_link, html_content)
    
    def _format_currency(self, value: float) -> str:
        """Template filter for currency formatting."""
        return f"${value:,.2f}"
    
    def _format_date(self, value: datetime, format: str = "%B %d, %Y") -> str:
        """Template filter for date formatting."""
        if isinstance(value, str):
            return value
        return value.strftime(format)
    
    # Legacy methods for backward compatibility
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
        # Build reset URL
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}&client_id={client_id}"
        
        # Use template if available, otherwise use inline HTML
        if self.jinja_env:
            result = await self.send_template_email(
                to=[email],
                subject="Password Reset Request",
                template_name="password_reset",
                context={
                    "reset_url": reset_url,
                    "expiration_hours": 1
                }
            )
        else:
            # Fallback to inline HTML
            html_body = f"""
            <html>
              <body>
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password. Click the link below to reset it:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>Or copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
              </body>
            </html>
            """
            plain_body = f"""
            Password Reset Request
            
            You requested to reset your password. Use the link below to reset it:
            
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you didn't request this, please ignore this email.
            """
            
            message = EmailMessage(
                to=[email],
                subject="Password Reset Request",
                html_content=html_body,
                text_content=plain_body
            )
            
            result = await self.send_email(message)
        
        return result.get("success", False)
