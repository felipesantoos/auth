"""
Audit Service Interface
Port for audit logging operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType


class IAuditService(ABC):
    """Interface for audit service operations"""
    
    @abstractmethod
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
        """Log an audit event"""
        pass
    
    @abstractmethod
    async def get_user_audit_logs(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for user"""
        pass
    
    @abstractmethod
    async def get_client_audit_logs(
        self,
        client_id: str,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 1000
    ) -> List[AuditLog]:
        """Get audit logs for client"""
        pass
    
    @abstractmethod
    async def get_security_events(
        self, client_id: str, days: int = 7, limit: int = 500
    ) -> List[AuditLog]:
        """Get security-critical events"""
        pass
    
    @abstractmethod
    async def detect_brute_force(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        threshold: int = 5,
        minutes: int = 30
    ) -> bool:
        """Detect brute-force attack"""
        pass
    
    @abstractmethod
    async def detect_suspicious_activity(
        self, user_id: str, client_id: str, ip_address: str, user_agent: str
    ) -> bool:
        """Detect suspicious activity"""
        pass

