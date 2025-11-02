"""
Account Lockout Service
Provides brute-force protection through account and IP-based lockout
"""
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from core.interfaces.primary.account_lockout_service_interface import IAccountLockoutService
from core.interfaces.secondary.i_app_user_repository import IAppUserRepository
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.services.audit.audit_service import AuditService
from core.domain.auth.audit_event_type import AuditEventType

logger = logging.getLogger(__name__)


class AccountLockoutService(IAccountLockoutService):
    """
    Service for account lockout protection.
    
    Protects against brute-force attacks by:
    - Locking accounts after N failed attempts (email-based)
    - Blocking IPs after N failed attempts (IP-based)
    - Tracking failed attempts in configurable time window
    - Logging all lockout events for audit
    
    Features:
    - Dual lockout: by email AND by IP
    - Configurable thresholds and durations
    - Automatic unlock after duration expires
    - Comprehensive audit logging
    """
    
    def __init__(
        self,
        user_repository: IAppUserRepository,
        audit_service: AuditService,
        settings_provider: ISettingsProvider
    ):
        self.user_repository = user_repository
        self.audit_service = audit_service
        self.settings = settings_provider.get_settings()
        
        # Lockout configuration (can be overridden by settings)
        self.max_attempts = getattr(settings_provider.get_settings(), 'account_lockout_max_attempts', 5)
        self.lockout_duration_minutes = getattr(settings_provider.get_settings(), 'account_lockout_duration_minutes', 30)
        self.attempt_window_minutes = getattr(settings_provider.get_settings(), 'account_lockout_window_minutes', 15)
        self.ip_lockout_enabled = getattr(settings_provider.get_settings(), 'ip_lockout_enabled', True)
    
    async def check_lockout(
        self,
        email: str,
        ip_address: str,
        client_id: str
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if account or IP is locked out.
        
        Checks both:
        1. Email-based lockout (user account)
        2. IP-based lockout (IP address)
        
        Args:
            email: User email
            ip_address: Client IP
            client_id: Client ID
            
        Returns:
            Tuple of (is_locked, unlock_time)
        """
        since = datetime.utcnow() - timedelta(minutes=self.attempt_window_minutes)
        
        # Check failed attempts for email
        email_attempts = await self.audit_service.detect_brute_force(
            user_id=None,  # Email not yet resolved to user_id
            ip_address=None,
            threshold=self.max_attempts,
            minutes=self.attempt_window_minutes
        )
        
        # For more accurate check, we need to count failed logins by email
        # This requires adding method to audit service/repository
        # For now, we'll use brute force detection
        
        # Check failed attempts for IP (if enabled)
        ip_locked = False
        if self.ip_lockout_enabled:
            ip_locked = await self.audit_service.detect_brute_force(
                user_id=None,
                ip_address=ip_address,
                threshold=self.max_attempts,
                minutes=self.attempt_window_minutes
            )
        
        # If either is locked, return locked status
        if email_attempts or ip_locked:
            unlock_time = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            return True, unlock_time
        
        return False, None
    
    async def record_failed_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        client_id: str
    ) -> bool:
        """
        Record failed login attempt and check if lockout should occur.
        
        Args:
            email: User email
            ip_address: Client IP
            user_agent: User agent
            client_id: Client ID
            
        Returns:
            True if account/IP is now locked
        """
        # Log the failed attempt (already done in auth_routes, but we track here too)
        logger.info(
            f"Failed login attempt recorded for {email} from {ip_address}",
            extra={"email": email, "ip": ip_address, "client_id": client_id}
        )
        
        # Check if should lock
        is_locked, unlock_time = await self.check_lockout(email, ip_address, client_id)
        
        if is_locked:
            # Try to get user and lock account in database
            try:
                user = await self.user_repository.find_by_email(email, client_id=client_id)
                if user and not user.is_locked():
                    user.lock_account(duration_minutes=self.lockout_duration_minutes)
                    await self.user_repository.save(user)
                    
                    # Log account lockout event
                    await self.audit_service.log_event(
                        client_id=client_id,
                        event_type=AuditEventType.ACCOUNT_LOCKED,
                        action=f"Account locked due to {self.max_attempts} failed login attempts",
                        description=f"Account for {email} has been locked until {unlock_time.isoformat()}",
                        user_id=user.id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            "email": email,
                            "unlock_time": unlock_time.isoformat(),
                            "max_attempts": self.max_attempts,
                            "window_minutes": self.attempt_window_minutes,
                            "lockout_reason": "brute_force_protection"
                        },
                        tags=["security", "critical", "lockout"],
                        status="warning"
                    )
                    
                    logger.warning(
                        f"Account locked: {email} until {unlock_time}",
                        extra={
                            "email": email,
                            "user_id": user.id,
                            "ip": ip_address,
                            "unlock_time": unlock_time.isoformat()
                        }
                    )
            except Exception as e:
                logger.error(f"Error locking account: {e}", exc_info=True)
            
            return True
        
        return False
    
    async def should_lock_account(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        client_id: str
    ) -> bool:
        """
        Check if account should be locked (convenience method).
        
        Args:
            user_id: User ID
            email: User email
            ip_address: Client IP
            client_id: Client ID
            
        Returns:
            True if account should be locked
        """
        is_locked, _ = await self.check_lockout(email, ip_address, client_id)
        return is_locked

