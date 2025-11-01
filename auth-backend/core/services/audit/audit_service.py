"""
Audit Service Implementation
Handles security event logging and analysis
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from core.interfaces.secondary.audit_log_repository_interface import IAuditLogRepository
from core.exceptions import DomainException

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for audit logging and security event tracking.
    
    This service is used by all other services to log security-relevant events.
    Follows OWASP logging best practices.
    """
    
    def __init__(self, repository: IAuditLogRepository):
        self.repository = repository
    
    async def log_event(
        self,
        client_id: str,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> AuditLog:
        """
        Log a security/audit event.
        
        Args:
            client_id: Client (tenant) ID
            event_type: Type of event
            user_id: Optional user ID (None for unauthenticated events)
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            ip_address: IP address of request
            user_agent: User agent string
            metadata: Additional event data
            status: Event status ('success', 'failure', 'warning')
            
        Returns:
            Created audit log
        """
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                client_id=client_id,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
                status=status,
                created_at=datetime.utcnow()
            )
            
            audit_log.validate()
            
            saved_log = await self.repository.save(audit_log)
            
            # Log to application logs as well
            log_level = logging.WARNING if status == "failure" else logging.INFO
            logger.log(
                log_level,
                f"Audit: {event_type.value} - User: {user_id}, Client: {client_id}, Status: {status}",
                extra={
                    "event_type": event_type.value,
                    "user_id": user_id,
                    "client_id": client_id,
                    "status": status,
                    "ip_address": ip_address
                }
            )
            
            return saved_log
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}", exc_info=True)
            # Don't fail the main operation if audit logging fails
            # But create a minimal audit log for debugging
            return AuditLog(
                id=None,
                user_id=user_id,
                client_id=client_id,
                event_type=event_type,
                status="error",
                metadata={"error": str(e)}
            )
    
    async def get_user_audit_logs(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID
            client_id: Optional client filter
            event_types: Optional event type filter
            days: Days to look back
            limit: Maximum results
            
        Returns:
            List of audit logs
        """
        try:
            return await self.repository.find_by_user(
                user_id=user_id,
                client_id=client_id,
                event_types=event_types,
                days=days,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting user audit logs: {e}", exc_info=True)
            return []
    
    async def get_client_audit_logs(
        self,
        client_id: str,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 1000
    ) -> List[AuditLog]:
        """
        Get audit logs for a client (admin view).
        
        Args:
            client_id: Client ID
            event_types: Optional event type filter
            days: Days to look back
            limit: Maximum results
            
        Returns:
            List of audit logs
        """
        try:
            return await self.repository.find_by_client(
                client_id=client_id,
                event_types=event_types,
                days=days,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting client audit logs: {e}", exc_info=True)
            return []
    
    async def get_security_events(
        self,
        client_id: str,
        days: int = 7,
        limit: int = 500
    ) -> List[AuditLog]:
        """
        Get security-critical events (admin view).
        
        Args:
            client_id: Client ID
            days: Days to look back
            limit: Maximum results
            
        Returns:
            List of security-critical audit logs
        """
        try:
            return await self.repository.find_security_events(
                client_id=client_id,
                days=days,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting security events: {e}", exc_info=True)
            return []
    
    async def detect_brute_force(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        threshold: int = 5,
        minutes: int = 30
    ) -> bool:
        """
        Detect brute-force attack attempts.
        
        Args:
            user_id: Optional user ID to check
            ip_address: Optional IP address to check
            threshold: Number of failed attempts to trigger (default 5)
            minutes: Time window in minutes (default 30)
            
        Returns:
            True if brute-force detected (should lock account/IP)
        """
        try:
            failed_count = await self.repository.count_failed_logins(
                user_id=user_id,
                ip_address=ip_address,
                minutes=minutes
            )
            
            is_attack = failed_count >= threshold
            
            if is_attack:
                logger.warning(
                    f"Brute-force attack detected - Failed logins: {failed_count}",
                    extra={
                        "user_id": user_id,
                        "ip_address": ip_address,
                        "failed_count": failed_count,
                        "threshold": threshold,
                        "minutes": minutes
                    }
                )
            
            return is_attack
            
        except Exception as e:
            logger.error(f"Error detecting brute-force: {e}", exc_info=True)
            # Fail closed: if we can't check, assume it might be an attack
            return True
    
    async def detect_suspicious_activity(
        self,
        user_id: str,
        client_id: str,
        ip_address: str,
        user_agent: str
    ) -> bool:
        """
        Detect suspicious activity patterns.
        
        Checks for:
        - Login from new location/device
        - Rapid login attempts from multiple IPs
        - Unusual activity patterns
        
        Args:
            user_id: User ID
            client_id: Client ID
            ip_address: Current IP address
            user_agent: Current user agent
            
        Returns:
            True if suspicious activity detected
        """
        try:
            # Get recent successful logins
            recent_logins = await self.repository.find_by_user(
                user_id=user_id,
                client_id=client_id,
                event_types=[AuditEventType.LOGIN_SUCCESS],
                days=30,
                limit=50
            )
            
            if not recent_logins:
                # First login ever - not suspicious
                return False
            
            # Check if this IP has been used before
            known_ips = {log.ip_address for log in recent_logins if log.ip_address}
            is_new_ip = ip_address not in known_ips
            
            # Check if this user agent has been used before
            known_agents = {log.user_agent for log in recent_logins if log.user_agent}
            is_new_agent = user_agent not in known_agents
            
            # Suspicious if both IP and user agent are new
            if is_new_ip and is_new_agent and len(recent_logins) > 3:
                logger.warning(
                    f"Suspicious activity: Login from new device/location",
                    extra={
                        "user_id": user_id,
                        "client_id": client_id,
                        "ip_address": ip_address,
                        "known_ips_count": len(known_ips),
                        "known_agents_count": len(known_agents)
                    }
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}", exc_info=True)
            return False

