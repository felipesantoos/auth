"""
Permission Domain Models
Fine-grained resource-level permissions
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class PermissionAction(str, Enum):
    """Permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"  # Full control


# ResourceType is now a FREE STRING!
# No enum needed - allows adding new resource types without code changes.
# Examples: "ticket", "project", "order", "invoice", "deal", "document", etc.
# Each system/client can define their own resource types dynamically.


@dataclass
class Permission:
    """
    Fine-grained permission model.
    
    Allows resource-level access control beyond basic RBAC.
    
    **Design Note**: resource_type is a FREE STRING (not enum) for maximum
    flexibility. Each system can define its own resource types without
    modifying the auth system code.
    """
    id: Optional[str] = None
    user_id: str = ""
    client_id: str = ""  # Multi-tenant
    resource_type: str = ""  # String livre! Pode ser "ticket", "invoice", "project", etc.
    resource_id: Optional[str] = None  # None = all resources of this type
    action: Optional[PermissionAction] = None
    granted_by: Optional[str] = None  # User who granted permission
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        # Normalize resource_type
        if self.resource_type:
            self.resource_type = self.resource_type.lower().strip()
    
    def allows(self, action: PermissionAction, resource_id: Optional[str] = None) -> bool:
        """Check if permission allows action on resource"""
        # MANAGE allows everything
        if self.action == PermissionAction.MANAGE:
            return True
        
        # Check action match
        if self.action != action:
            return False
        
        # Check resource (if permission is resource-specific)
        if self.resource_id and resource_id and self.resource_id != resource_id:
            return False
        
        return True

