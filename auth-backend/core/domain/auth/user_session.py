"""
User Session Domain Model
Represents an active user session across devices
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from core.exceptions import MissingRequiredFieldException, BusinessRuleException


@dataclass
class UserSession:
    """
    Domain model for user sessions.
    
    Tracks user sessions across multiple devices for security and management.
    Each session is associated with a refresh token.
    """
    id: Optional[str]
    user_id: str
    client_id: str
    refresh_token_hash: str  # bcrypt hash of the refresh token
    device_name: Optional[str] = None
    device_type: Optional[str] = None  # 'mobile', 'desktop', 'tablet', 'unknown'
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None  # City, Country
    last_activity: Optional[datetime] = None
    created_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate session according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
        """
        if not self.user_id or not self.user_id.strip():
            raise MissingRequiredFieldException("user_id")
        
        if not self.client_id or not self.client_id.strip():
            raise MissingRequiredFieldException("client_id")
        
        if not self.refresh_token_hash or not self.refresh_token_hash.strip():
            raise MissingRequiredFieldException("refresh_token_hash")
    
    def is_active(self) -> bool:
        """Check if session is active (not revoked and not expired)"""
        if self.revoked_at is not None:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_revoked(self) -> bool:
        """Check if session was revoked"""
        return self.revoked_at is not None
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def revoke(self) -> None:
        """
        Revoke this session (logout).
        
        Raises:
            BusinessRuleException: If session was already revoked
        """
        if self.revoked_at is not None:
            raise BusinessRuleException(
                "Session has already been revoked",
                "SESSION_ALREADY_REVOKED"
            )
        
        self.revoked_at = datetime.utcnow()
    
    def get_device_description(self) -> str:
        """Get human-readable device description"""
        if self.device_name:
            return self.device_name
        
        if self.device_type:
            return self.device_type.capitalize()
        
        return "Unknown Device"
    
    def get_location_description(self) -> str:
        """Get human-readable location description"""
        return self.location if self.location else "Unknown Location"

