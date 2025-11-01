"""
API Key Scopes
Enumeration of permissions that can be granted to API keys
"""
from enum import Enum


class ApiKeyScope(str, Enum):
    """
    Scopes (permissions) that can be assigned to API keys.
    
    API keys provide programmatic access with fine-grained permissions.
    Following principle of least privilege - grant only necessary permissions.
    """
    # User Scopes
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    DELETE_USER = "delete:user"
    
    # Resource Scopes (generic for future resources)
    READ_RESOURCE = "read:resource"
    WRITE_RESOURCE = "write:resource"
    DELETE_RESOURCE = "delete:resource"
    
    # Session Scopes
    READ_SESSION = "read:session"
    MANAGE_SESSION = "manage:session"
    
    # Admin Scopes
    ADMIN = "admin"
    
    # Audit Scopes
    READ_AUDIT = "read:audit"
    
    def is_read_only(self) -> bool:
        """Check if scope is read-only"""
        return self.value.startswith("read:")
    
    def is_write_scope(self) -> bool:
        """Check if scope allows writing"""
        return "write:" in self.value or "manage:" in self.value or "delete:" in self.value
    
    def is_admin_scope(self) -> bool:
        """Check if this is an admin scope"""
        return self == self.ADMIN

