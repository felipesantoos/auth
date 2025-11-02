"""
Suspicious Activity Detector Service
Detects suspicious authentication patterns and security anomalies
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from core.interfaces.primary.suspicious_activity_detector_interface import ISuspiciousActivityDetector
from core.services.audit.audit_service import AuditService
from core.domain.auth.audit_event_type import AuditEventType

logger = logging.getLogger(__name__)


class SuspiciousActivityDetector(ISuspiciousActivityDetector):
    """
    Service for detecting suspicious activity patterns.
    
    Detection methods:
    - Impossible travel: Logins from distant locations in short time
    - New device: Login from previously unseen device/IP
    - Location changes: Significant location changes
    - Pattern anomalies: Unusual login patterns
    
    Uses audit logs to analyze historical patterns and detect anomalies.
    """
    
    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service
        self.impossible_travel_hours = 2  # Flag if locations change in < 2 hours
        self.lookback_days = 30  # Check last 30 days of login history
    
    async def check_location_change(
        self,
        user_id: str,
        client_id: str,
        current_location: str,
        current_ip: str
    ) -> bool:
        """
        Detect impossible travel (login from distant locations in short time).
        
        Args:
            user_id: User ID
            client_id: Client ID
            current_location: Current login location
            current_ip: Current IP address
            
        Returns:
            True if suspicious location change detected
        """
        if not current_location:
            return False
        
        try:
            # Get recent successful logins
            recent_logins = await self.audit_service.get_user_audit_logs(
                user_id=user_id,
                client_id=client_id,
                event_types=[AuditEventType.LOGIN_SUCCESS],
                days=self.lookback_days,
                limit=10
            )
            
            if not recent_logins:
                return False
            
            # Check for impossible travel
            for log in recent_logins:
                if not log.location or log.location == current_location:
                    continue
                
                # Calculate time difference
                if log.created_at:
                    time_diff_hours = (datetime.utcnow() - log.created_at).total_seconds() / 3600
                    
                    # If different location and within impossible travel window
                    if time_diff_hours < self.impossible_travel_hours:
                        logger.warning(
                            f"Impossible travel detected: {user_id} from {log.location} to {current_location} in {time_diff_hours:.2f} hours",
                            extra={
                                "user_id": user_id,
                                "previous_location": log.location,
                                "current_location": current_location,
                                "time_diff_hours": time_diff_hours,
                                "previous_ip": log.ip_address,
                                "current_ip": current_ip
                            }
                        )
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking location change: {e}", exc_info=True)
            return False
    
    async def check_new_device(
        self,
        user_id: str,
        client_id: str,
        user_agent: str,
        ip_address: str
    ) -> bool:
        """
        Check if login is from a new device.
        
        Args:
            user_id: User ID
            client_id: Client ID
            user_agent: User agent string
            ip_address: IP address
            
        Returns:
            True if this is a new device/IP combination
        """
        try:
            # Get recent successful logins
            recent_logins = await self.audit_service.get_user_audit_logs(
                user_id=user_id,
                client_id=client_id,
                event_types=[AuditEventType.LOGIN_SUCCESS],
                days=self.lookback_days,
                limit=20
            )
            
            if not recent_logins:
                # First login ever - not suspicious
                return False
            
            # Check if IP and user agent combination is new
            known_ips = {log.ip_address for log in recent_logins if log.ip_address}
            known_agents = {log.user_agent for log in recent_logins if log.user_agent}
            
            is_new_ip = ip_address not in known_ips
            is_new_agent = user_agent not in known_agents
            
            # If both IP and user agent are new, it's a new device
            if is_new_ip and is_new_agent:
                logger.info(
                    f"New device detected for user {user_id}",
                    extra={
                        "user_id": user_id,
                        "ip_address": ip_address,
                        "user_agent": user_agent[:100],  # Truncate for logging
                        "known_ips_count": len(known_ips),
                        "known_agents_count": len(known_agents)
                    }
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking new device: {e}", exc_info=True)
            return False
    
    async def detect_impossible_travel(
        self,
        user_id: str,
        client_id: str,
        current_location: str
    ) -> bool:
        """
        Detect impossible travel based on previous login locations.
        
        This is an alias for check_location_change for backward compatibility.
        
        Args:
            user_id: User ID
            client_id: Client ID
            current_location: Current location
            
        Returns:
            True if impossible travel detected
        """
        # For impossible travel, we need the current IP as well
        # This is a simplified version
        return await self.check_location_change(
            user_id=user_id,
            client_id=client_id,
            current_location=current_location,
            current_ip=""  # We don't have it in this signature
        )
    
    async def detect_suspicious_activity(
        self,
        user_id: str,
        client_id: str,
        ip_address: str,
        user_agent: str,
        location: Optional[str] = None
    ) -> bool:
        """
        Comprehensive suspicious activity detection.
        
        Combines multiple detection methods:
        1. New device detection
        2. Location change / impossible travel (if location available)
        3. Other pattern anomalies
        
        Args:
            user_id: User ID
            client_id: Client ID
            ip_address: IP address
            user_agent: User agent
            location: Optional location
            
        Returns:
            True if suspicious activity detected
        """
        try:
            # Check for new device (IP + user agent combination)
            is_new_device = await self.check_new_device(
                user_id=user_id,
                client_id=client_id,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Check for impossible travel (if location available)
            is_impossible_travel = False
            if location:
                is_impossible_travel = await self.check_location_change(
                    user_id=user_id,
                    client_id=client_id,
                    current_location=location,
                    current_ip=ip_address
                )
            
            # Consider it suspicious if:
            # - Impossible travel detected (high severity)
            # - New device from new location (medium severity)
            
            if is_impossible_travel:
                logger.warning(
                    f"Suspicious activity: Impossible travel detected for user {user_id}",
                    extra={
                        "user_id": user_id,
                        "client_id": client_id,
                        "ip_address": ip_address,
                        "location": location
                    }
                )
                return True
            
            # New device alone is not necessarily suspicious (users get new devices)
            # But we flag it for monitoring
            if is_new_device and location:
                logger.info(
                    f"New device login for user {user_id} from {location}",
                    extra={
                        "user_id": user_id,
                        "client_id": client_id,
                        "ip_address": ip_address,
                        "location": location,
                        "severity": "info"
                    }
                )
                # Return False - new device is not suspicious by itself
                # Only log for admin monitoring
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}", exc_info=True)
            return False

