"""
Audit Log Domain Model
Represents a security/audit event in the system
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from .audit_event_type import AuditEventType
from core.exceptions import MissingRequiredFieldException


@dataclass
class AuditLog:
    """
    Domain model for audit logging.
    
    Tracks all security-relevant events for compliance, debugging, and security analysis.
    Follows OWASP logging best practices.
    """
    id: Optional[str]
    user_id: Optional[str]  # None for unauthenticated events (failed login)
    client_id: str
    event_type: AuditEventType
    resource_type: Optional[str] = None  # 'user', 'session', 'api_key', etc.
    resource_id: Optional[str] = None  # ID of affected resource
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Additional event-specific data
    status: str = "success"  # 'success', 'failure', 'warning'
    created_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate audit log according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
        """
        if not self.client_id or not self.client_id.strip():
            raise MissingRequiredFieldException("client_id")
        
        if not self.event_type:
            raise MissingRequiredFieldException("event_type")
        
        if not self.status or not self.status.strip():
            raise MissingRequiredFieldException("status")
    
    def is_success(self) -> bool:
        """Check if event was successful"""
        return self.status == "success"
    
    def is_failure(self) -> bool:
        """Check if event failed"""
        return self.status == "failure"
    
    def is_warning(self) -> bool:
        """Check if event is a warning"""
        return self.status == "warning"
    
    def is_security_critical(self) -> bool:
        """Check if this is a security-critical event"""
        return self.event_type.is_security_critical()
    
    def get_summary(self) -> str:
        """Get human-readable event summary"""
        event_name = self.event_type.value.replace("_", " ").title()
        
        if self.user_id:
            return f"{event_name} by user {self.user_id}"
        
        return event_name
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the audit log"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

