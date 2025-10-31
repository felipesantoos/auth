"""
Authentication Service Implementation
Orchestrates authentication logic with JWT and bcrypt
Adapted for multi-tenant architecture
"""
import logging
import re
from typing import Optional, Tuple
from datetime import datetime, timedelta
import bcrypt
import jwt
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.primary.password_reset_service_interface import IPasswordResetService
from core.interfaces.primary.oauth_service_interface import IOAuthService
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.interfaces.secondary.email_service_interface import EmailServiceInterface
from core.interfaces.secondary.cache_service_interface import CacheServiceInterface
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole

logger = logging.getLogger(__name__)


class AuthService(IAuthService, IPasswordResetService, IOAuthService):
    """
    Service implementation - orchestrates authentication logic.
    
    Following:
    - Single Responsibility (only authentication logic)
    - Dependency Inversion (depends on interfaces)
    - Open/Closed (extend via new methods)
    - Multi-tenant: All operations respect client isolation
    """
    
    def __init__(
        self,
        repository: AppUserRepositoryInterface,
        cache_service: CacheServiceInterface,
        settings_provider: SettingsProviderInterface,
        email_service: Optional[EmailServiceInterface] = None
    ):
        """
        Constructor injection for testability.
        
        Args:
            repository: Repository interface (injected)
            cache_service: Cache service interface (injected)
            settings_provider: Settings provider interface (injected)
            email_service: Optional email service for sending emails
        """
        self.repository = repository
        self.cache = cache_service
        self.settings = settings_provider
        self.email_service = email_service
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    
    def _validate_password_strength(self, password: str) -> None:
        """
        Validate password strength.
        
        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password):
            raise ValueError("Password must contain at least one number")
    
    def _generate_token(self, user_id: str, token_type: str, client_id: Optional[str] = None) -> str:
        """
        Generate JWT token with client_id in payload (multi-tenant).
        
        Args:
            user_id: User ID
            token_type: Token type ("access" or "refresh")
            client_id: Client (tenant) ID
        """
        now = datetime.utcnow()
        
        if token_type == "access":
            exp = now + timedelta(minutes=self.settings.get_access_token_expire_minutes())
        else:  # refresh
            exp = now + timedelta(days=self.settings.get_refresh_token_expire_days())
        
        payload = {
            "user_id": user_id,
            "type": token_type,
            "iat": now,
            "exp": exp,
            "iss": self.settings.get_jwt_issuer(),
            "aud": self.settings.get_jwt_audience(),
        }
        
        # Multi-tenant: Include client_id in token payload for tenant isolation
        if client_id:
            payload["client_id"] = client_id
        
        return jwt.encode(
            payload,
            self.settings.get_jwt_secret(),
            algorithm=self.settings.get_jwt_algorithm()
        )
    
    def _resolve_client_id_from_token(
        self, payload: dict, provided_client_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolve client_id from token payload or provided parameter.
        
        Multi-tenant security: We validate that provided client_id matches token's client_id
        if both are present, to prevent token theft across tenants.
        
        Args:
            payload: JWT token payload
            provided_client_id: Optional client_id provided from request
            
        Returns:
            Resolved client_id or None if not found
        """
        token_client_id = payload.get("client_id")
        if provided_client_id and token_client_id and provided_client_id != token_client_id:
            return None  # Client mismatch - security violation
        return provided_client_id or token_client_id
    
    async def _generate_and_store_refresh_token(
        self, user_id: str, refresh_token: str, client_id: str
    ) -> None:
        """
        Store refresh token in Redis with multi-tenant isolation.
        
        We prefix cache keys with client_id to ensure tokens are isolated per tenant,
        preventing cross-tenant token reuse attacks.
        
        Args:
            user_id: User ID
            refresh_token: Refresh token string
            client_id: Client (tenant) ID for cache key prefix
        """
        ttl_seconds = self.settings.get_refresh_token_expire_days() * 24 * 60 * 60
        cache_key = f"{client_id}:refresh_token:{refresh_token}"
        await self.cache.set(cache_key, user_id, ttl=ttl_seconds)
    
    async def _generate_and_store_tokens(
        self, user_id: str, client_id: str
    ) -> Tuple[str, str]:
        """
        Generate both access and refresh tokens, and store refresh token.
        
        We generate both tokens together to ensure they're consistent (same client_id),
        and store only the refresh token in Redis to enable revocation.
        
        Args:
            user_id: User ID
            client_id: Client (tenant) ID
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        access_token = self._generate_token(user_id, "access", client_id)
        refresh_token = self._generate_token(user_id, "refresh", client_id)
        await self._generate_and_store_refresh_token(user_id, refresh_token, client_id)
        return access_token, refresh_token
    
    async def _validate_login_credentials(
        self, email: str, password: str, client_id: str
    ) -> AppUser:
        """
        Validate login credentials and return user if valid.
        
        Security: We check user exists, belongs to client, is active, and password matches.
        All errors return the same message to prevent user enumeration attacks.
        
        Args:
            email: User email
            password: Plain text password
            client_id: Client (tenant) ID
            
        Returns:
            Validated user
            
        Raises:
            ValueError: If credentials are invalid (generic message for security)
        """
        user = await self.repository.find_by_email(email, client_id=client_id)
        if not user or user.client_id != client_id or not user.active:
            raise ValueError("Invalid email or password")
        
        if not self._verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        return user
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.settings.get_jwt_secret(),
                algorithms=[self.settings.get_jwt_algorithm()],
                audience=self.settings.get_jwt_audience(),
                issuer=self.settings.get_jwt_issuer(),
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def login(
        self, email: str, password: str, client_id: str
    ) -> Tuple[str, str, AppUser]:
        """
        Authenticate user and generate tokens (multi-tenant).
        
        Args:
            email: User email
            password: Plain text password
            client_id: Client (tenant) ID for multi-tenant isolation
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            ValueError: If credentials are invalid or user doesn't belong to client
        """
        user = await self._validate_login_credentials(email, password, client_id)
        access_token, refresh_token = await self._generate_and_store_tokens(user.id, client_id)
        
        logger.info("Login successful", extra={"user_id": user.id, "client_id": client_id})
        return access_token, refresh_token, user
    
    async def logout(self, refresh_token: str, client_id: Optional[str] = None) -> bool:
        """
        Logout user by invalidating refresh token (multi-tenant).
        
        Args:
            refresh_token: Refresh token to invalidate
            client_id: Optional client ID for validation
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return False
        
        client_id_to_use = self._resolve_client_id_from_token(payload, client_id)
        if not client_id_to_use:
            return False
        
        # Revoke token by deleting from Redis (enables immediate logout)
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        await self.cache.delete(cache_key)
        
        logger.info("Logout successful", extra={"user_id": payload.get("user_id"), "client_id": client_id_to_use})
        return True
    
    async def _validate_refresh_token(
        self, refresh_token: str, client_id: Optional[str] = None
    ) -> Tuple[dict, str, str]:
        """
        Validate refresh token and return payload, client_id, and user_id.
        
        Security: We verify token is valid, not revoked, and belongs to the correct tenant.
        Token rotation requires revoking the old token immediately after validation.
        
        Args:
            refresh_token: Refresh token string
            client_id: Optional client ID for validation
            
        Returns:
            Tuple of (payload, client_id, user_id)
            
        Raises:
            ValueError: If token is invalid, revoked, or user is inactive
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        client_id_to_use = self._resolve_client_id_from_token(payload, client_id)
        if not client_id_to_use:
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Check if token exists in Redis (not revoked) - validates token hasn't been logged out
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        stored_user_id = await self.cache.get(cache_key)
        if not stored_user_id or stored_user_id != user_id:
            logger.warning("Refresh token not found in Redis or revoked", extra={"client_id": client_id_to_use})
            raise ValueError("Refresh token has been revoked")
        
        # Verify user still exists and is active (user might have been deactivated)
        user = await self.repository.find_by_id(user_id, client_id=client_id_to_use)
        if not user or not user.active:
            raise ValueError("User not found or inactive")
        
        return payload, client_id_to_use, user_id
    
    async def refresh_access_token(
        self, refresh_token: str, client_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate new access token using refresh token (multi-tenant with token rotation).
        
        Token rotation: We generate a new refresh token and revoke the old one immediately
        to limit the window of vulnerability if a token is compromised.
        
        Args:
            refresh_token: Refresh token
            client_id: Optional client ID for validation
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        payload, client_id_to_use, user_id = await self._validate_refresh_token(refresh_token, client_id)
        
        # Generate new tokens (token rotation for security)
        new_access_token, new_refresh_token = await self._generate_and_store_tokens(
            user_id, client_id_to_use
        )
        
        # Revoke old refresh token (token rotation - one token valid at a time)
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        await self.cache.delete(cache_key)
        
        logger.info("Token refresh successful", extra={"user_id": user_id, "client_id": client_id_to_use})
        return new_access_token, new_refresh_token
    
    async def register(
        self, username: str, email: str, password: str, name: str, client_id: str
    ) -> AppUser:
        """
        Register new user (multi-tenant).
        
        Args:
            username: Username
            email: User email
            password: Plain text password
            name: User full name
            client_id: Client (tenant) ID
            
        Returns:
            Created user
        """
        # Check if email already exists within client (multi-tenant)
        existing = await self.repository.find_by_email(email, client_id=client_id)
        if existing:
            raise ValueError(f"Email '{email}' is already registered for this client")
        
        # Validate password strength
        self._validate_password_strength(password)
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user (default role is USER)
        user = AppUser(
            id=None,
            username=username,
            email=email,
            password_hash=password_hash,
            name=name,
            role=UserRole.USER,
            client_id=client_id,  # Multi-tenant
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Validate
        user.validate()
        
        # Save
        return await self.repository.save(user)
    
    async def change_password(
        self, user_id: str, old_password: str, new_password: str, client_id: Optional[str] = None
    ) -> bool:
        """
        Change user password (multi-tenant).
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            client_id: Optional client ID for validation
        """
        # Get user with client_id filtering (multi-tenant)
        user = await self.repository.find_by_id(user_id, client_id=client_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not self._verify_password(old_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Validate new password strength
        self._validate_password_strength(new_password)
        
        # Hash and update
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        await self.repository.save(user)
        
        # Revoke all refresh tokens for this user (security: password changed)
        if user.client_id:
            pattern = f"{user.client_id}:refresh_token:*"
            # Note: This is a best-effort revocation - we can't iterate over all tokens efficiently
            # A better approach would be to store user_id in the token cache value and use sets
            # For now, we'll rely on token expiration
        
        logger.info("Password changed successfully", extra={"user_id": user_id, "client_id": user.client_id})
        return True
    
    # ========== Password Reset Operations ==========
    
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
        
        reset_token = self._generate_reset_token(user.id, user.email, client_id)
        await self._store_reset_token(reset_token, user.id, client_id)
        
        # Send email (non-blocking - token is valid even if email fails)
        if self.email_service:
            try:
                await self.email_service.send_password_reset_email(email, reset_token, client_id)
                logger.info("Password reset email sent", extra={"user_id": user.id, "client_id": client_id})
            except Exception as e:
                logger.error(f"Failed to send password reset email: {str(e)}", extra={"user_id": user.id}, exc_info=True)
        
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
        
        # Check if token exists in Redis (validates single-use - delete after successful reset)
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
    
    # ========== OAuth2 Operations ==========
    
    async def _create_or_update_oauth_user(
        self, email: str, name: str, client_id: str, provider: str
    ) -> AppUser:
        """
        Create new OAuth user or update existing user's name.
        
        OAuth users get a random password since they authenticate via provider.
        If user exists, we update their name in case it changed on the OAuth provider.
        
        Args:
            email: User email from OAuth provider
            name: User name from OAuth provider
            client_id: Client (tenant) ID
            provider: OAuth provider name (for logging)
            
        Returns:
            User object (created or updated)
        """
        user = await self.repository.find_by_email(email, client_id=client_id)
        
        if not user:
            # Create new OAuth user with random password (never used for auth)
            import uuid
            username = email.split('@')[0]  # Use email prefix as username
            random_password = str(uuid.uuid4())
            password_hash = self._hash_password(random_password)
            
            user = AppUser(
                id=None,
                username=username,
                email=email,
                password_hash=password_hash,
                name=name,
                role=UserRole.USER,
                client_id=client_id,
                active=True
            )
            user.validate()
            user = await self.repository.save(user)
            logger.info("New user created via OAuth", extra={"user_id": user.id, "provider": provider, "client_id": client_id})
        else:
            # Update name if changed on OAuth provider
            if user.name != name:
                user.name = name
                user = await self.repository.save(user)
            logger.info("Existing user logged in via OAuth", extra={"user_id": user.id, "provider": provider, "client_id": client_id})
        
        return user
    
    async def oauth_login(
        self,
        provider: str,
        email: str,
        name: str,
        oauth_id: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> Tuple[str, str, AppUser]:
        """
        Login or register user via OAuth2 (multi-tenant).
        
        Creates user if doesn't exist, or logs in existing user.
        
        Args:
            provider: OAuth provider name (e.g., 'google', 'github')
            email: User email from OAuth provider
            name: User name from OAuth provider
            oauth_id: Optional OAuth provider user ID
            client_id: Client (tenant) ID for multi-tenant isolation
            
        Returns:
            Tuple of (access_token, refresh_token, user)
        """
        if not client_id:
            raise ValueError("Client ID is required for OAuth login (multi-tenant)")
        
        logger.info("OAuth login attempt", extra={"provider": provider, "email": email, "client_id": client_id})
        
        user = await self._create_or_update_oauth_user(email, name, client_id, provider)
        
        if not user.active:
            raise ValueError("User account is deactivated")
        
        access_token, refresh_token = await self._generate_and_store_tokens(user.id, client_id)
        return access_token, refresh_token, user
    
    async def get_current_user(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get current user by ID (multi-tenant).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for validation
        """
        return await self.repository.find_by_id(user_id, client_id=client_id)
    
    # ========== Admin Operations ==========
    
    async def list_all_users(self, client_id: Optional[str] = None) -> list[AppUser]:
        """
        List all users (admin only, filtered by client_id if provided).
        
        Args:
            client_id: Optional client ID to filter users
        """
        from core.domain.auth.user_filter import UserFilter
        
        filter_obj = UserFilter(client_id=client_id) if client_id else None
        return await self.repository.find_all(filter=filter_obj)
    
    async def get_user_by_email(self, email: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get user by email (admin only, multi-tenant).
        
        Args:
            email: User email
            client_id: Optional client ID for filtering
        """
        return await self.repository.find_by_email(email, client_id=client_id)
    
    async def get_user_by_id(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get user by ID (admin only, multi-tenant).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for filtering
        """
        return await self.repository.find_by_id(user_id, client_id=client_id)
    
    async def admin_update_user(self, user: AppUser) -> AppUser:
        """
        Update user (admin only).
        
        Args:
            user: User domain object with updated fields
        """
        user.updated_at = datetime.utcnow()
        return await self.repository.save(user)
    
    async def admin_delete_user(self, user_id: str, admin_id: str, client_id: Optional[str] = None) -> bool:
        """
        Delete user (admin only, multi-tenant).
        Prevents self-deletion.
        
        Args:
            user_id: ID of user to delete
            admin_id: ID of admin performing the deletion
            client_id: Optional client ID for validation
        """
        if user_id == admin_id:
            raise ValueError("Cannot delete your own account")
        
        return await self.repository.delete(user_id, client_id=client_id)

