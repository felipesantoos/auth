"""
WebAuthn Credential Domain Model
Represents a WebAuthn/Passkey credential for biometric authentication
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from core.exceptions import MissingRequiredFieldException, BusinessRuleException


@dataclass
class WebAuthnCredential:
    """
    Domain model for WebAuthn credentials (Passkeys).
    
    WebAuthn provides passwordless authentication using biometrics, security keys,
    or platform authenticators (Face ID, Touch ID, Windows Hello, etc.)
    
    Following WebAuthn specification and security best practices.
    """
    id: Optional[str]
    user_id: str
    client_id: str
    credential_id: str  # Unique credential ID from WebAuthn
    public_key: str  # Public key for verification (base64 encoded)
    counter: int = 0  # Sign counter to prevent replay attacks
    aaguid: Optional[str] = None  # Authenticator Attestation GUID
    device_name: Optional[str] = None  # User-friendly device name
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate WebAuthn credential according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
        """
        if not self.user_id or not self.user_id.strip():
            raise MissingRequiredFieldException("user_id")
        
        if not self.client_id or not self.client_id.strip():
            raise MissingRequiredFieldException("client_id")
        
        if not self.credential_id or not self.credential_id.strip():
            raise MissingRequiredFieldException("credential_id")
        
        if not self.public_key or not self.public_key.strip():
            raise MissingRequiredFieldException("public_key")
    
    def is_active(self) -> bool:
        """Check if credential is active (not revoked)"""
        return self.revoked_at is None
    
    def is_revoked(self) -> bool:
        """Check if credential was revoked"""
        return self.revoked_at is not None
    
    def revoke(self) -> None:
        """
        Revoke this WebAuthn credential.
        
        Raises:
            BusinessRuleException: If credential was already revoked
        """
        if self.revoked_at is not None:
            raise BusinessRuleException(
                "WebAuthn credential has already been revoked",
                "WEBAUTHN_CREDENTIAL_ALREADY_REVOKED"
            )
        
        self.revoked_at = datetime.utcnow()
    
    def update_last_used(self) -> None:
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
    
    def increment_counter(self) -> None:
        """
        Increment sign counter.
        
        Counter is used to detect cloned authenticators.
        If counter doesn't increase, it indicates potential security issue.
        """
        self.counter += 1
    
    def verify_counter(self, new_counter: int) -> bool:
        """
        Verify that new counter is greater than stored counter.
        
        This prevents replay attacks and detects cloned authenticators.
        
        Args:
            new_counter: Counter value from authentication assertion
            
        Returns:
            True if counter is valid (greater than stored counter)
        """
        return new_counter > self.counter
    
    def update_counter(self, new_counter: int) -> None:
        """
        Update counter after successful authentication.
        
        Args:
            new_counter: New counter value
            
        Raises:
            BusinessRuleException: If new counter is not greater than current
        """
        if not self.verify_counter(new_counter):
            raise BusinessRuleException(
                "Invalid counter value - possible cloned authenticator detected",
                "WEBAUTHN_INVALID_COUNTER"
            )
        
        self.counter = new_counter
    
    def get_device_description(self) -> str:
        """Get human-readable device description"""
        if self.device_name:
            return self.device_name
        
        return "Security Key"

