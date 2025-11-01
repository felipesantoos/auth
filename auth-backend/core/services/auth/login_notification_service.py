"""
Login Notification Service
Sends email notifications for new logins
"""
import logging
from typing import Optional
from datetime import datetime

from core.domain.auth.app_user import AppUser
from core.domain.auth.user_session import UserSession
from core.domain.auth.audit_event_type import AuditEventType
from core.interfaces.secondary.email_service_interface import IEmailService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.services.audit.audit_service import AuditService

logger = logging.getLogger(__name__)


class LoginNotificationService:
    """
    Service for sending login notification emails.
    
    Notifies users when a new login is detected from a different device or location.
    Only sends notifications for genuinely new devices/IPs to avoid spam.
    """
    
    def __init__(
        self,
        email_service: IEmailService,
        settings_provider: ISettingsProvider
    ):
        self.email_service = email_service
        self.settings = settings_provider.get_settings()
    
    async def should_send_notification(
        self,
        user_id: str,
        client_id: str,
        current_ip: str,
        current_user_agent: str,
        audit_service: AuditService
    ) -> bool:
        """
        Check if login notification should be sent.
        
        Only send if this is a new device or new IP.
        
        Args:
            user_id: User ID
            client_id: Client ID
            current_ip: Current IP address
            current_user_agent: Current user agent
            audit_service: Audit service to query recent logins
            
        Returns:
            True if notification should be sent
        """
        # Get recent successful logins
        recent_logins = await audit_service.get_user_audit_logs(
            user_id=user_id,
            client_id=client_id,
            event_types=[AuditEventType.LOGIN_SUCCESS],
            days=30,
            limit=20
        )
        
        if not recent_logins or len(recent_logins) <= 1:
            # First login ever or second login - don't spam
            return False
        
        # Check if this IP/device was seen before
        known_ips = {log.ip_address for log in recent_logins if log.ip_address}
        known_agents = {log.user_agent for log in recent_logins if log.user_agent}
        
        is_new_ip = current_ip not in known_ips
        is_new_device = current_user_agent not in known_agents
        
        # Send notification only for genuinely new device/IP combination
        return is_new_ip or is_new_device
    
    async def send_new_login_notification(
        self,
        user: AppUser,
        session: UserSession
    ) -> None:
        """
        Send email notification for new login.
        
        Args:
            user: User who logged in
            session: Session information (device, IP, location, etc)
        """
        logger.info(f"Sending login notification to {user.email}")
        
        # Format time
        login_time = session.created_at.strftime("%Y-%m-%d %H:%M UTC") if session.created_at else "Unknown"
        
        # Generate HTML email
        html_content = self._generate_email_html(
            user_name=user.name,
            device_name=session.device_name or "Unknown Device",
            device_type=session.device_type or "unknown",
            ip_address=session.ip_address or "Unknown",
            location=session.location or "Unknown",
            time=login_time
        )
        
        # Send email
        try:
            await self.email_service.send_email(
                to_email=user.email,
                subject="New login to your account",
                html_content=html_content
            )
            logger.info(f"Login notification sent successfully to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send login notification: {e}", exc_info=True)
            # Don't fail the login if email fails
    
    def _generate_email_html(
        self,
        user_name: str,
        device_name: str,
        device_type: str,
        ip_address: str,
        location: str,
        time: str
    ) -> str:
        """Generate HTML email content"""
        frontend_url = self.settings.cors_origins_list[0] if self.settings.cors_origins_list else "http://localhost:5173"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>New Login Detected</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .info-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; }}
        .button {{ display: inline-block; background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>New Login Detected</h1>
        
        <p>Hello {user_name},</p>
        
        <div class="alert">
            <strong>⚠️ A new login was detected on your account.</strong>
        </div>
        
        <p>If this was you, you can safely ignore this email.</p>
        
        <div class="info-box">
            <h3>Login Details:</h3>
            <div class="info-row">
                <span class="label">Device:</span> {device_name} ({device_type})
            </div>
            <div class="info-row">
                <span class="label">Location:</span> {location}
            </div>
            <div class="info-row">
                <span class="label">IP Address:</span> {ip_address}
            </div>
            <div class="info-row">
                <span class="label">Time:</span> {time}
            </div>
        </div>
        
        <p><strong>If this wasn't you:</strong></p>
        <ul>
            <li>Change your password immediately</li>
            <li>Enable multi-factor authentication</li>
            <li>Review your active sessions</li>
            <li>Contact support if you need help</li>
        </ul>
        
        <a href="{frontend_url}/security" class="button">Secure My Account</a>
        
        <div style="margin-top: 30px; font-size: 12px; color: #666;">
            <p>This is an automated security notification.</p>
            <p>© 2025 {self.settings.app_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """

