"""
Authentication Service Implementation
Implements IAuthService - core authentication operations (login, logout, register, etc.)
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.interfaces.secondary.cache_service_interface import CacheServiceInterface
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.domain.auth.user_filter import UserFilter
from .auth_service_base import AuthServiceBase

logger = logging.getLogger(__name__)


class AuthService(AuthServiceBase, IAuthService):
    """
    Service implementation for core authentication operations.
    
    Implements only IAuthService interface following Single Responsibility Principle.
    """
    
    def __init__(
        self,
        repository: AppUserRepositoryInterface,
        cache_service: CacheServiceInterface,
        settings_provider: SettingsProviderInterface,
    ):
        """
        Constructor for AuthService.
        
        Args:
            repository: Repository interface for user operations
            cache_service: Cache service interface
            settings_provider: Settings provider interface
        """
        super().__init__(cache_service, settings_provider)
        self.repository = repository
    
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
    
    async def list_all_users(self, client_id: Optional[str] = None) -> list[AppUser]:
        """
        List all users (admin only, filtered by client_id if provided).
        
        Args:
            client_id: Optional client ID to filter users
        """
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

