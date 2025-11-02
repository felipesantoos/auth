"""
Comprehensive Audit Log Domain Model
Tracks all user and system actions with full context for compliance and security
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from .audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory
from core.exceptions import MissingRequiredFieldException


@dataclass
class AuditLog:
    """
    Comprehensive audit log entry.
    
    Tracks all user and system actions with complete context including:
    - Who performed the action (user, admin, system)
    - What was affected (resource type/ID)
    - When it happened (timestamp)
    - Where it came from (IP, location, user agent)
    - How it changed (before/after state, field-level changes)
    - Why it happened (metadata, context)
    
    Used for:
    - Compliance (GDPR, SOX, HIPAA, ISO 27001)
    - Security (forensics, intrusion detection)
    - Debugging (track state changes)
    - Analytics (user behavior, feature usage)
    """
    
    # ===== Identification =====
    id: Optional[str] = None  # Database ID
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique event UUID
    
    # ===== Event Details =====
    event_type: AuditEventType = None
    event_category: Optional[AuditEventCategory] = None  # Auto-calculated from event_type
    action: str = ""  # Human-readable action (e.g., "Created project 'Website Redesign'")
    description: str = ""  # Detailed description (optional)
    
    # ===== Actor (who) =====
    user_id: Optional[str] = None  # User who performed action (None for unauthenticated)
    username: Optional[str] = None  # Username for display
    user_email: Optional[str] = None  # User email
    impersonated_by: Optional[str] = None  # Admin ID if impersonating user
    
    # ===== Multi-tenant =====
    client_id: str = ""  # Client (tenant) ID
    
    # ===== Resource (what) =====
    resource_type: Optional[str] = None  # "project", "document", "user", etc.
    resource_id: Optional[str] = None  # ID of affected resource
    resource_name: Optional[str] = None  # Name/title for display
    
    # ===== Context (where, when, how) =====
    ip_address: Optional[str] = None  # Client IP address
    user_agent: Optional[str] = None  # Browser/client user agent
    location: Optional[str] = None  # Geolocation (e.g., "São Paulo, Brazil")
    request_id: Optional[str] = None  # Request correlation ID
    session_id: Optional[str] = None  # User session ID
    
    # ===== Changes (before/after) =====
    changes: Optional[List[Dict[str, Any]]] = None  # [{field, old_value, new_value, change_type}]
    old_values: Optional[Dict[str, Any]] = None  # Complete old state (snapshot)
    new_values: Optional[Dict[str, Any]] = None  # Complete new state (snapshot)
    
    # ===== Additional Context =====
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional event data
    tags: List[str] = field(default_factory=list)  # ["sensitive", "compliance", "critical", "pii"]
    
    # ===== Status =====
    success: bool = True  # Whether action was successful
    status: str = "success"  # "success", "failure", "warning" (legacy compat)
    error_message: Optional[str] = None  # Error details if failed
    
    # ===== Timestamps =====
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Set created_at if not provided
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        # Auto-calculate event_category from event_type
        if self.event_type and not self.event_category:
            self.event_category = self.event_type.get_category()
        
        # Auto-generate event_id if not provided
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        
        # Sync status and success fields
        if not self.success and self.status == "success":
            self.status = "failure"
        elif self.success and self.status in ["failure", "error"]:
            self.success = False
    
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
    
    # ===== Status Check Methods =====
    
    def is_success(self) -> bool:
        """Check if event was successful"""
        return self.success and self.status == "success"
    
    def is_failure(self) -> bool:
        """Check if event failed"""
        return not self.success or self.status == "failure"
    
    def is_warning(self) -> bool:
        """Check if event is a warning"""
        return self.status == "warning"
    
    def is_security_critical(self) -> bool:
        """Check if this is a security-critical event"""
        return self.event_type.is_security_critical() if self.event_type else False
    
    # ===== Tag-based Checks =====
    
    def is_sensitive(self) -> bool:
        """Check if this event involves sensitive data (PII, PHI, financial)"""
        return "sensitive" in self.tags or "pii" in self.tags or "phi" in self.tags
    
    def is_critical(self) -> bool:
        """Check if this is a critical event (admin action, deletion, etc.)"""
        return "critical" in self.tags or self.is_security_critical()
    
    def requires_compliance(self) -> bool:
        """Check if this event requires compliance tracking (GDPR, SOX, HIPAA)"""
        return "compliance" in self.tags or "gdpr" in self.tags or "sox" in self.tags or "hipaa" in self.tags
    
    # ===== Resource Checks =====
    
    def involves_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Check if this event involves a specific entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            
        Returns:
            True if event involves this entity
        """
        return self.resource_type == entity_type and self.resource_id == entity_id
    
    # ===== Change Tracking Methods =====
    
    def get_changed_fields(self) -> List[str]:
        """
        Get list of field names that changed.
        
        Returns:
            List of field names
        """
        if not self.changes:
            return []
        return [change.get("field") for change in self.changes if "field" in change]
    
    def get_change_summary(self) -> str:
        """
        Get human-readable summary of changes.
        
        Returns:
            String like "email: old → new; name: Old → New"
        """
        if not self.changes:
            return "No changes"
        
        summaries = []
        for change in self.changes[:5]:  # Limit to 5 for brevity
            field = change.get("field", "unknown")
            old = change.get("old_value", "None")
            new = change.get("new_value", "None")
            summaries.append(f"{field}: {old} → {new}")
        
        if len(self.changes) > 5:
            summaries.append(f"...and {len(self.changes) - 5} more change(s)")
        
        return "; ".join(summaries)
    
    def has_changes(self) -> bool:
        """Check if this event has field-level changes"""
        return self.changes is not None and len(self.changes) > 0
    
    # ===== Display Methods =====
    
    def get_summary(self) -> str:
        """
        Get human-readable event summary.
        
        Returns:
            Summary string for display
        """
        if self.action:
            return self.action
        
        event_name = self.event_type.value.replace("_", " ").title() if self.event_type else "Unknown Event"
        
        if self.user_id and self.username:
            return f"{event_name} by {self.username}"
        elif self.user_id:
            return f"{event_name} by user {self.user_id}"
        
        return event_name
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the audit log.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
    
    def add_tag(self, tag: str) -> None:
        """
        Add tag to the audit log.
        
        Args:
            tag: Tag to add
        """
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def add_tags(self, tags: List[str]) -> None:
        """
        Add multiple tags to the audit log.
        
        Args:
            tags: List of tags to add
        """
        for tag in tags:
            self.add_tag(tag)
