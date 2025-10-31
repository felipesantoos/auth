"""
Authentication Service Implementation
Orchestrates authentication logic with JWT and bcrypt
Adapted for multi-tenant architecture
"""
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
import bcrypt
import jwt
from core.interfaces.primary.auth_service_interface import AuthServiceInterface
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from config.settings import settings
from infra.redis.cache_service import CacheService

logger = logging.getLogger(__name__)


class AuthService(AuthServiceInterface):
    """
    Service implementation - orchestrates authentication logic.
    
    Following:
    - Single Responsibility (only authentication logic)
    - Dependency Inversion (depends on interfaces)
    - Open/Closed (extend via new methods)
    - Multi-tenant: All operations respect client isolation
    """
    
    def __init__(self, repository: AppUserRepositoryInterface):
        """
        Constructor injection for testability.
        
        Args:
            repository: Repository interface (injected)
        """
        self.repository = repository
        self.cache = CacheService()
    
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
            exp = now + timedelta(minutes=settings.access_token_expire_minutes)
        else:  # refresh
            exp = now + timedelta(days=settings.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "type": token_type,
            "iat": now,
            "exp": exp,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        }
        
        # Multi-tenant: Include client_id in token payload
        if client_id:
            payload["client_id"] = client_id
        
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
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
        # Find user by email within client (multi-tenant)
        user = await self.repository.find_by_email(email, client_id=client_id)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify user belongs to client
        if user.client_id != client_id:
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.active:
            raise ValueError("User account is deactivated")
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Generate tokens with client_id
        access_token = self._generate_token(user.id, "access", client_id)
        refresh_token = self._generate_token(user.id, "refresh", client_id)
        
        # Store refresh token in Redis with client_id prefix (multi-tenant isolation)
        ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
        cache_key = f"{client_id}:refresh_token:{refresh_token}"
        await self.cache.set(cache_key, user.id, ttl=ttl_seconds)
        
        logger.info("Login successful", extra={"user_id": user.id, "client_id": client_id})
        return access_token, refresh_token, user
    
    async def logout(self, refresh_token: str, client_id: Optional[str] = None) -> bool:
        """
        Logout user by invalidating refresh token (multi-tenant).
        
        Args:
            refresh_token: Refresh token to invalidate
            client_id: Optional client ID for validation
        """
        # Verify token
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return False
        
        # Multi-tenant: Extract and validate client_id
        token_client_id = payload.get("client_id")
        if client_id and token_client_id != client_id:
            return False
        
        # Use token's client_id if client_id not provided
        client_id_to_use = client_id or token_client_id
        if not client_id_to_use:
            return False
        
        # Delete refresh token from Redis (revoke token)
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        await self.cache.delete(cache_key)
        
        logger.info("Logout successful", extra={"user_id": payload.get("user_id"), "client_id": client_id_to_use})
        return True
    
    async def refresh_access_token(
        self, refresh_token: str, client_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate new access token using refresh token (multi-tenant).
        
        Args:
            refresh_token: Refresh token
            client_id: Optional client ID for validation
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        # Multi-tenant: Extract and validate client_id
        token_client_id = payload.get("client_id")
        if client_id and token_client_id != client_id:
            raise ValueError("Invalid refresh token")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Check if token exists in Redis (not revoked) - multi-tenant
        client_id_to_use = client_id or token_client_id
        if not client_id_to_use:
            raise ValueError("Invalid refresh token - missing client_id")
        
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        stored_user_id = await self.cache.get(cache_key)
        if not stored_user_id or stored_user_id != user_id:
            logger.warning("Refresh token not found in Redis or revoked", extra={"client_id": client_id_to_use})
            raise ValueError("Refresh token has been revoked")
        
        # Verify user still exists and is active
        user = await self.repository.find_by_id(user_id, client_id=token_client_id)
        if not user or not user.active:
            raise ValueError("User not found or inactive")
        
        # Generate new tokens with client_id (token rotation)
        new_access_token = self._generate_token(user_id, "access", token_client_id)
        new_refresh_token = self._generate_token(user_id, "refresh", token_client_id)
        
        # Store new refresh token in Redis with client_id prefix
        ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
        new_cache_key = f"{client_id_to_use}:refresh_token:{new_refresh_token}"
        await self.cache.set(new_cache_key, user_id, ttl=ttl_seconds)
        
        # Delete old refresh token from Redis (revoke - token rotation)
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
        
        # Validate password
        if len(password) < 6:
            raise ValueError("Password must have at least 6 characters")
        
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
        
        # Validate new password
        if len(new_password) < 6:
            raise ValueError("New password must have at least 6 characters")
        
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
        from core.services.filters.app_user_filter import AppUserFilter
        
        filter_obj = AppUserFilter(client_id=client_id) if client_id else None
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

