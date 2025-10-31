"""
App User Domain Model
Represents a system user with authentication and authorization
Adapted for multi-tenant architecture with client_id
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from .user_role import UserRole


@dataclass
class AppUser:
    """
    Domain model for application user.
    
    This is pure business logic with no framework dependencies.
    Following Single Responsibility Principle.
    
    Multi-tenant: Each user belongs to a client (tenant).
    """
    id: Optional[str]
    username: str
    email: str
    password_hash: str
    name: str
    role: UserRole
    client_id: Optional[str]  # Multi-tenant: client (tenant) ID
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Business validation rules"""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must have at least 3 characters")
        
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address")
        
        if not self.name or len(self.name) < 2:
            raise ValueError("Name must have at least 2 characters")
        
        if not self.password_hash:
            raise ValueError("Password hash is required")
        
        if not self.client_id:
            raise ValueError("Client ID is required (multi-tenant)")
    
    def activate(self) -> None:
        """Business operation to activate user"""
        self.active = True
    
    def deactivate(self) -> None:
        """Business operation to deactivate user"""
        self.active = False
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN
    
    def is_manager(self) -> bool:
        """Check if user has manager role"""
        return self.role == UserRole.MANAGER
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def belongs_to_client(self, client_id: str) -> bool:
        """Check if user belongs to a specific client"""
        return self.client_id == client_id

