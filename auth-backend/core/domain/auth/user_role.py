"""
User Role Enum
Defines user access levels in the system
"""
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    
    def __str__(self) -> str:
        return self.value

