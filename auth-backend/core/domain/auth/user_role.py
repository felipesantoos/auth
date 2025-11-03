"""
User Role Enum
Defines user roles in the system
"""
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    
    def __str__(self) -> str:
        """String representation returns the value"""
        return self.value

