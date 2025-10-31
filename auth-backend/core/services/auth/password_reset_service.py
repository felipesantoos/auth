"""
Password Reset Service Implementation
Implements IPasswordResetService - password reset operations
"""
import logging
from typing import Tuple
from datetime import datetime, timedelta
import jwt
from core.interfaces.primary.password_reset_service_interface import IPasswordResetService
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.interfaces.secondary.cache_service_interface import CacheServiceInterface
from core.interfaces.secondary.email_service_interface import EmailServiceInterface
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.domain.auth.app_user import AppUser
from .auth_service_base import AuthServiceBase

logger = logging.getLogger(__name__)


class PasswordResetService(AuthServiceBase, IPasswordResetService):
    """
    Service implementation for password reset operations.
    
    Implements only IPasswordResetService interface following Single Responsibility Principle.
    """
    
    def __init__(
        self,
        repository: AppUserRepositoryInterface,
        cache_service: CacheServiceInterface,
        settings_provider: SettingsProviderInterface,
        email_service: EmailServiceInterface,
    ):
        """
        Constructor for PasswordResetService.
        
        Args:
            repository: Repository interface for user operations
            cache_service: Cache service interface
            settings_provider: Settings provider interface
            email_service: Email service interface for sending reset emails
        """
        super().__init__(cache_service, settings_provider)
        self.repository = repository
        self.email_service = email_service
    
    def _generate_reset_token(self, user_id: str, email: str, client_id: str) -> str:
        """
        Generate password reset token with 1 hour expiry.
        
        We use a short expiry (1 hour) for reset tokens to limit the window of attack
        if a reset link is intercepted or leaked.
        
        Args:
            user_id: User ID
            email: User email
            client_id: Client (tenant) ID
            
        Returns:
            Reset token string
        """
        now = datetime.utcnow()
        exp = now + timedelta(hours=1)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "type": "password_reset",
            "client_id": client_id,
            "iat": now,
            "exp": exp,
            "iss": self.settings.get_jwt_issuer(),
            "aud": self.settings.get_jwt_audience(),
        }
        
        return jwt.encode(
            payload,
            self.settings.get_jwt_secret(),
            algorithm=self.settings.get_jwt_algorithm()
        )
    
    async def _store_reset_token(self, reset_token: str, user_id: str, client_id: str) -> None:
        """
        Store reset token in Redis with 1 hour TTL.
        
        We store tokens in Redis to enable one-time use (delete after successful reset)
        and to allow revocation if needed.
        
        Args:
            reset_token: Reset token string
            user_id: User ID
            client_id: Client (tenant) ID
        """
        cache_key = f"password_reset:{client_id}:{reset_token}"
        ttl_seconds = 60 * 60  # 1 hour
        await self.cache.set(cache_key, user_id, ttl=ttl_seconds)
    
    async def _process_password_reset_for_user(self, user: AppUser, client_id: str) -> None:
        """
        Generate reset token and send email for valid user.
        
        Non-blocking email sending - token is valid even if email fails.
        
        Args:
            user: Valid active user
            client_id: Client (tenant) ID
        """
        reset_token = self._generate_reset_token(user.id, user.email, client_id)
        await self._store_reset_token(reset_token, user.id, client_id)
        
        try:
            await self.email_service.send_password_reset_email(user.email, reset_token, client_id)
            logger.info("Password reset email sent", extra={"user_id": user.id, "client_id": client_id})
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}", extra={"user_id": user.id}, exc_info=True)
    
    async def forgot_password(self, email: str, client_id: str) -> bool:
        """
        Request password reset (generate reset token) (multi-tenant).
        
        Security: Always returns True to prevent user enumeration attacks.
        We don't reveal whether an email exists in the system.
        
        Args:
            email: User email address
            client_id: Client (tenant) ID for multi-tenant isolation
            
        Returns:
            True (always, for security)
        """
        logger.info("Password reset request", extra={"email": email, "client_id": client_id})
        
        user = await self.repository.find_by_email(email, client_id=client_id)
        
        # Security: Always return True to prevent user enumeration
        if not user or not user.active:
            if not user:
                logger.warning("Password reset requested for non-existent email", extra={"email": email, "client_id": client_id})
            else:
                logger.warning("Password reset requested for inactive user", extra={"user_id": user.id, "client_id": client_id})
            return True
        
        await self._process_password_reset_for_user(user, client_id)
        return True
    
    async def _validate_reset_token(
        self, reset_token: str, client_id: str
    ) -> Tuple[str, AppUser]:
        """
        Validate reset token and return user_id and user.
        
        Security: We verify token is valid, not expired, not already used, and belongs
        to the correct tenant. Reset tokens are single-use only.
        
        Args:
            reset_token: Reset token string
            client_id: Client (tenant) ID for validation
            
        Returns:
            Tuple of (user_id, user)
            
        Raises:
            ValueError: If token is invalid, expired, used, or user is inactive
        """
        payload = self.verify_token(reset_token)
        if not payload or payload.get("type") != "password_reset":
            raise ValueError("Invalid or expired reset token")
        
        token_client_id = payload.get("client_id")
        if token_client_id != client_id:
            raise ValueError("Invalid reset token - client mismatch")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Invalid reset token payload")
        
        cache_key = f"password_reset:{client_id}:{reset_token}"
        stored_user_id = await self.cache.get(cache_key)
        if not stored_user_id or stored_user_id != user_id:
            logger.warning("Password reset token not found in Redis or already used", extra={"client_id": client_id})
            raise ValueError("Reset token has been used or expired")
        
        user = await self.repository.find_by_id(user_id, client_id=client_id)
        if not user or not user.active:
            raise ValueError("User not found or account is deactivated")
        
        return user_id, user
    
    async def _update_password_and_revoke_tokens(
        self, user: AppUser, new_password: str, reset_token: str, client_id: str
    ) -> None:
        """
        Update user password and revoke reset token.
        
        After password change, we revoke the reset token (single-use) and ideally would
        revoke all refresh tokens, but we rely on expiration for efficiency.
        
        Args:
            user: User to update
            new_password: New plain text password
            reset_token: Reset token to revoke
            client_id: Client (tenant) ID
        """
        self._validate_password_strength(new_password)
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.utcnow()
        await self.repository.save(user)
        
        # Revoke reset token (single-use - prevents reuse)
        cache_key = f"password_reset:{client_id}:{reset_token}"
        await self.cache.delete(cache_key)
        
        # Note: Revoking all refresh tokens would require iterating Redis keys,
        # which is inefficient. We rely on token expiration instead.
    
    async def reset_password(self, reset_token: str, new_password: str, client_id: str) -> bool:
        """
        Reset password using reset token (multi-tenant, single-use token).
        
        Args:
            reset_token: Password reset token from forgot_password
            new_password: New password to set
            client_id: Client (tenant) ID for validation
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If reset token is invalid, expired, or already used
        """
        logger.info("Password reset attempt", extra={"client_id": client_id})
        
        user_id, user = await self._validate_reset_token(reset_token, client_id)
        await self._update_password_and_revoke_tokens(user, new_password, reset_token, client_id)
        
        logger.info("Password reset successful", extra={"user_id": user_id, "client_id": client_id})
        return True

