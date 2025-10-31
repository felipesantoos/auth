"""
Email Service Implementation
SMTP-based email sending service
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from core.interfaces.secondary.email_service_interface import EmailServiceInterface
from config.settings import settings

logger = logging.getLogger(__name__)


class EmailService(EmailServiceInterface):
    """
    SMTP email service implementation.
    
    Sends emails using SMTP server configured in settings.
    Falls back to logging if SMTP is not configured (for development).
    """
    
    def __init__(self):
        """Initialize email service"""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port or 587
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        
    def _is_configured(self) -> bool:
        """Check if SMTP is configured"""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)
    
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
        # Build reset URL (frontend will handle the token)
        # In production, this should use the frontend URL from settings
        reset_url = f"http://localhost:5173/reset-password?token={reset_token}&client_id={client_id}"
        
        subject = "Password Reset Request"
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
        
        return await self.send_email(
            to=email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send generic email via SMTP.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self._is_configured():
            # Log email instead of sending (development mode)
            logger.warning(
                "SMTP not configured - logging email instead of sending",
                extra={
                    "to": to,
                    "subject": subject,
                    "smtp_host": self.smtp_host
                }
            )
            logger.info(f"Email would be sent to {to}: {subject}\n{body}")
            return True  # Return True to not break flow in development
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = to
            
            # Add plain text part
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            
            # Add HTML part if provided
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info("Email sent successfully", extra={"to": to, "subject": subject})
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send email: {str(e)}",
                extra={"to": to, "subject": subject},
                exc_info=True
            )
            return False

