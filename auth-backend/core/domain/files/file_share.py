"""
File Share Domain Model
Represents file sharing permissions with business logic
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
from core.exceptions import (
    MissingRequiredFieldException,
    ValidationException,
    InvalidValueException
)


class FilePermission(str, Enum):
    """File sharing permission levels."""
    READ = "read"
    WRITE = "write"


@dataclass
class FileShare:
    """
    Domain model for file sharing.
    
    Represents permission granted to a user to access another user's file.
    """
    id: Optional[str]
    file_id: str
    shared_by: str  # User ID who owns the file
    shared_with: str  # User ID who receives access
    permission: FilePermission
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate entity according to business rules.
        
        Raises:
            ValidationException: If validation fails
        """
        # Required fields
        if not self.file_id or not self.file_id.strip():
            raise MissingRequiredFieldException("file_id")
        
        if not self.shared_by or not self.shared_by.strip():
            raise MissingRequiredFieldException("shared_by")
        
        if not self.shared_with or not self.shared_with.strip():
            raise MissingRequiredFieldException("shared_with")
        
        # Cannot share with self
        if self.shared_by == self.shared_with:
            raise ValidationException("Cannot share file with yourself")
        
        # Permission validation
        if self.permission not in [FilePermission.READ, FilePermission.WRITE]:
            raise InvalidValueException(
                "permission",
                self.permission,
                "must be 'read' or 'write'"
            )
        
        # Expiration validation
        if self.expires_at and self.expires_at < datetime.utcnow():
            raise ValidationException("Expiration date cannot be in the past")
    
    def is_expired(self) -> bool:
        """Check if share has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if share is currently active (not expired)."""
        return not self.is_expired()
    
    def has_read_permission(self) -> bool:
        """Check if share grants read permission."""
        return True  # Both READ and WRITE include read access
    
    def has_write_permission(self) -> bool:
        """Check if share grants write permission."""
        return self.permission == FilePermission.WRITE
    
    def extend_expiration(self, hours: int) -> None:
        """
        Extend expiration by specified hours.
        
        Args:
            hours: Number of hours to extend
        """
        if not self.expires_at:
            # If no expiration set, set it from now
            self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        else:
            self.expires_at += timedelta(hours=hours)
    
    def set_expiration(self, hours: int) -> None:
        """
        Set expiration to specified hours from now.
        
        Args:
            hours: Number of hours until expiration
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def revoke(self) -> None:
        """Revoke the share by setting expiration to now."""
        self.expires_at = datetime.utcnow()
    
    def upgrade_to_write(self) -> None:
        """Upgrade permission from READ to WRITE."""
        self.permission = FilePermission.WRITE
    
    def downgrade_to_read(self) -> None:
        """Downgrade permission from WRITE to READ."""
        self.permission = FilePermission.READ

