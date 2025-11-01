"""
Audit Log Repository Interface
Port for audit log persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType


class AuditLogRepositoryInterface(ABC):
    """Interface for audit log repository operations"""
    
    @abstractmethod
    async def save(self, audit_log: AuditLog) -> AuditLog:
        """Save audit log"""
        pass
    
    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """Find audit logs for a user"""
        pass
    
    @abstractmethod
    async def find_by_client(
        self,
        client_id: str,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 1000
    ) -> List[AuditLog]:
        """Find audit logs for a client"""
        pass
    
    @abstractmethod
    async def find_security_events(
        self,
        client_id: str,
        days: int = 7,
        limit: int = 500
    ) -> List[AuditLog]:
        """Find security-critical events"""
        pass
    
    @abstractmethod
    async def count_failed_logins(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        minutes: int = 30
    ) -> int:
        """Count failed login attempts for brute-force detection"""
        pass

