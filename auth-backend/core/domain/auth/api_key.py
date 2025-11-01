"""
API Key Domain Model
Represents a personal access token for API authentication
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
from .api_key_scope import ApiKeyScope
from core.exceptions import (
    MissingRequiredFieldException,
    BusinessRuleException,
    InvalidValueException,
)


@dataclass
class ApiKey:
    """
    Domain model for API keys (Personal Access Tokens).
    
    API keys provide programmatic access to the API with fine-grained permissions.
    Security considerations:
    - Keys are hashed in database (only shown once during creation)
    - Keys have expiration dates
    - Keys can be revoked at any time
    - Keys have specific scopes (permissions)
    """
    id: Optional[str]
    user_id: str
    client_id: str
    name: str  # User-friendly name for the key
    key_hash: str  # bcrypt hash of the actual key
    scopes: List[ApiKeyScope] = field(default_factory=list)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate API key according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
            InvalidValueException: If values are invalid
        """
        if not self.user_id or not self.user_id.strip():
            raise MissingRequiredFieldException("user_id")
        
        if not self.client_id or not self.client_id.strip():
            raise MissingRequiredFieldException("client_id")
        
        if not self.name or not self.name.strip():
            raise MissingRequiredFieldException("name")
        
        if len(self.name) < 3:
            raise InvalidValueException("name", self.name, "must be at least 3 characters")
        
        if len(self.name) > 100:
            raise InvalidValueException("name", self.name, "must not exceed 100 characters")
        
        if not self.key_hash or not self.key_hash.strip():
            raise MissingRequiredFieldException("key_hash")
        
        if not self.scopes or len(self.scopes) == 0:
            raise InvalidValueException("scopes", "[]", "must have at least one scope")
    
    def is_active(self) -> bool:
        """Check if API key is active (not revoked and not expired)"""
        if self.revoked_at is not None:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def is_expired(self) -> bool:
        """Check if API key has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_revoked(self) -> bool:
        """Check if API key was revoked"""
        return self.revoked_at is not None
    
    def revoke(self) -> None:
        """
        Revoke this API key.
        
        Raises:
            BusinessRuleException: If key was already revoked
        """
        if self.revoked_at is not None:
            raise BusinessRuleException(
                "API key has already been revoked",
                "API_KEY_ALREADY_REVOKED"
            )
        
        self.revoked_at = datetime.utcnow()
    
    def update_last_used(self) -> None:
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
    
    def has_scope(self, scope: ApiKeyScope) -> bool:
        """Check if API key has a specific scope"""
        # Admin scope grants all permissions
        if ApiKeyScope.ADMIN in self.scopes:
            return True
        
        return scope in self.scopes
    
    def has_any_scope(self, scopes: List[ApiKeyScope]) -> bool:
        """Check if API key has any of the specified scopes"""
        # Admin scope grants all permissions
        if ApiKeyScope.ADMIN in self.scopes:
            return True
        
        return any(scope in self.scopes for scope in scopes)
    
    def has_all_scopes(self, scopes: List[ApiKeyScope]) -> bool:
        """Check if API key has all of the specified scopes"""
        # Admin scope grants all permissions
        if ApiKeyScope.ADMIN in self.scopes:
            return True
        
        return all(scope in self.scopes for scope in scopes)
    
    def get_scopes_list(self) -> List[str]:
        """Get list of scope values as strings"""
        return [scope.value for scope in self.scopes]
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new API key.
        
        Format: ask_{32_bytes_hex}
        
        Returns:
            The generated key (should be shown to user only once)
        """
        random_bytes = secrets.token_hex(32)
        return f"ask_{random_bytes}"

