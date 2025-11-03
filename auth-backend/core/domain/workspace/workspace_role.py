"""
Workspace Role Enum
Defines user access levels within a workspace
"""
from enum import Enum


class WorkspaceRole(str, Enum):
    """Workspace role enumeration - defines access levels per workspace"""
    
    ADMIN = "admin"      # Full control over workspace
    MANAGER = "manager"  # Can manage users and settings
    USER = "user"        # Regular workspace member
    
    def __str__(self) -> str:
        return self.value

