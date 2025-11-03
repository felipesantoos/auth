"""
App User Domain Model
Represents a system user with authentication and authorization
Adapted for multi-tenant architecture with client_id
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta
import re
import secrets
# REMOVED: from .user_role import UserRole (roles now in WorkspaceMember)
from core.exceptions import (
    MissingRequiredFieldException,
    InvalidEmailException,
    InvalidValueException,
    ValidationException,
    InvalidTokenException,
    TokenExpiredException,
)


@dataclass
class AppUser:
    """
    Domain model for application user.
    
    This is pure business logic with no framework dependencies.
    Following Single Responsibility Principle and Encapsulation.
    
    Multi-workspace: Users have global identity and can belong to multiple workspaces.
    Roles are now per-workspace (via WorkspaceMember).
    
    Encapsulation: password_hash is protected and accessed via property and controlled methods.
    """
    id: Optional[str]
    username: str
    email: str
    name: str
    # REMOVED: role (now in WorkspaceMember - roles are per workspace)
    # REMOVED: client_id (now via workspace_member or user_client)
    _password_hash: str = field(repr=False, init=True)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Email Verification
    email_verified: bool = False
    email_verification_token: Optional[str] = None
    email_verification_sent_at: Optional[datetime] = None
    
    # MFA/2FA
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    
    # Account Security
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Passwordless Auth
    magic_link_token: Optional[str] = None
    magic_link_sent_at: Optional[datetime] = None
    
    # Avatar / Profile Picture
    avatar_url: Optional[str] = None
    
    # KYC (Know Your Customer) / Identity Verification
    kyc_document_id: Optional[str] = None
    kyc_status: Optional[str] = None  # pending, approved, rejected
    kyc_verified_at: Optional[datetime] = None
    
    @property
    def password_hash(self) -> str:
        """Read-only access to password hash (encapsulation)"""
        return self._password_hash
    
    def change_password_hash(self, new_password_hash: str) -> None:
        """
        Change password hash (controlled modification).
        
        This method enforces that password hash changes go through proper validation.
        Services should hash passwords before calling this method.
        
        Args:
            new_password_hash: New hashed password
            
        Raises:
            ValidationException: If password hash is empty
        """
        if not new_password_hash:
            raise MissingRequiredFieldException("password_hash")
        self._password_hash = new_password_hash
    
    def validate(self) -> None:
        """
        Validate entity according to business rules.
        
        Raises:
            ValidationException: If validation fails
        """
        # Required fields
        if not self.username or not self.username.strip():
            raise MissingRequiredFieldException("username")
        
        if not self.email or not self.email.strip():
            raise MissingRequiredFieldException("email")
        
        if not self.name or not self.name.strip():
            raise MissingRequiredFieldException("name")
        
        # Email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, self.email):
            raise InvalidEmailException(self.email)
        
        # Username length
        if len(self.username) < 3:
            raise InvalidValueException("username", self.username, "must be at least 3 characters")
        
        if len(self.username) > 255:
            raise InvalidValueException("username", self.username, "must not exceed 255 characters")
        
        # Name length
        if len(self.name) < 2:
            raise InvalidValueException("name", self.name, "must be at least 2 characters")
        
        if len(self.name) > 255:
            raise InvalidValueException("name", self.name, "must not exceed 255 characters")
        
        # Email length
        if len(self.email) > 255:
            raise InvalidValueException("email", self.email, "must not exceed 255 characters")
        
        # Password hash required
        if not self._password_hash:
            raise MissingRequiredFieldException("password_hash")
    
    def activate(self) -> None:
        """Business operation to activate user"""
        self.active = True
    
    def deactivate(self) -> None:
        """Business operation to deactivate user"""
        self.active = False
    
    # REMOVED: is_admin(), is_manager(), can_manage_users() - now in WorkspaceMember
    # REMOVED: belongs_to_client() - access is now via user_client or workspace_client
    
    # Email Verification Methods
    def generate_email_verification_token(self) -> str:
        """
        Generate a new email verification token.
        
        Returns:
            The generated token (should be sent to user via email)
        """
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token
    
    def verify_email_token(self, token: str, expire_hours: int = 24) -> bool:
        """
        Verify email verification token.
        
        Args:
            token: Token to verify
            expire_hours: Hours until token expires (default 24)
            
        Returns:
            True if token is valid and not expired
            
        Raises:
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token has expired
        """
        if not self.email_verification_token or self.email_verification_token != token:
            raise InvalidTokenException("Invalid email verification token")
        
        if not self.email_verification_sent_at:
            raise InvalidTokenException("Email verification token not found")
        
        # Check if token has expired
        expiration_time = self.email_verification_sent_at + timedelta(hours=expire_hours)
        if datetime.utcnow() > expiration_time:
            raise TokenExpiredException("Email verification token has expired")
        
        return True
    
    def mark_email_verified(self) -> None:
        """
        Mark user's email as verified and clear verification token.
        """
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
    
    def is_email_verified(self) -> bool:
        """Check if user's email is verified"""
        return self.email_verified
    
    # MFA Methods
    def enable_mfa(self, secret: str) -> None:
        """
        Enable MFA for this user.
        
        Args:
            secret: TOTP secret key
        """
        self.mfa_enabled = True
        self.mfa_secret = secret
    
    def disable_mfa(self) -> None:
        """Disable MFA for this user"""
        self.mfa_enabled = False
        self.mfa_secret = None
    
    def has_mfa_enabled(self) -> bool:
        """Check if user has MFA enabled"""
        return self.mfa_enabled
    
    # Account Security Methods
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts counter"""
        self.failed_login_attempts += 1
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock account for specified duration.
        
        Args:
            duration_minutes: How long to lock account (default 30 minutes)
        """
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def reset_failed_login_attempts(self) -> None:
        """Reset failed login attempts counter and unlock account"""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    # Passwordless Auth Methods
    def generate_magic_link_token(self) -> str:
        """
        Generate a new magic link token for passwordless authentication.
        
        Returns:
            The generated token (should be sent to user via email)
        """
        self.magic_link_token = secrets.token_urlsafe(32)
        self.magic_link_sent_at = datetime.utcnow()
        return self.magic_link_token
    
    def verify_magic_link_token(self, token: str, expire_minutes: int = 15) -> bool:
        """
        Verify magic link token.
        
        Args:
            token: Token to verify
            expire_minutes: Minutes until token expires (default 15)
            
        Returns:
            True if token is valid and not expired
            
        Raises:
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token has expired
        """
        if not self.magic_link_token or self.magic_link_token != token:
            raise InvalidTokenException("Invalid magic link token")
        
        if not self.magic_link_sent_at:
            raise InvalidTokenException("Magic link token not found")
        
        # Check if token has expired
        expiration_time = self.magic_link_sent_at + timedelta(minutes=expire_minutes)
        if datetime.utcnow() > expiration_time:
            raise TokenExpiredException("Magic link has expired")
        
        return True
    
    def clear_magic_link_token(self) -> None:
        """Clear magic link token after successful use"""
        self.magic_link_token = None
        self.magic_link_sent_at = None
    
    # Avatar Methods
    def update_avatar(self, avatar_url: str) -> None:
        """
        Update user's avatar URL.
        
        Args:
            avatar_url: URL to avatar image
        """
        self.avatar_url = avatar_url
    
    def remove_avatar(self) -> None:
        """Remove user's avatar."""
        self.avatar_url = None
    
    def has_avatar(self) -> bool:
        """Check if user has avatar set."""
        return self.avatar_url is not None
    
    # KYC Methods
    def submit_kyc_document(self, document_id: str) -> None:
        """
        Submit KYC document for verification.
        
        Args:
            document_id: ID of uploaded document file
        """
        self.kyc_document_id = document_id
        self.kyc_status = "pending"
        self.kyc_verified_at = None
    
    def approve_kyc(self) -> None:
        """Approve KYC verification (admin only)."""
        self.kyc_status = "approved"
        self.kyc_verified_at = datetime.utcnow()
    
    def reject_kyc(self, reason: str = None) -> None:
        """
        Reject KYC verification (admin only).
        
        Args:
            reason: Optional reason for rejection
        """
        self.kyc_status = "rejected"
        self.kyc_verified_at = None
        # Reason could be stored in a separate field or audit log
    
    def is_kyc_verified(self) -> bool:
        """Check if user has completed KYC verification."""
        return self.kyc_status == "approved"
    
    def kyc_pending(self) -> bool:
        """Check if KYC is pending review."""
        return self.kyc_status == "pending"

