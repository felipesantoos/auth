"""
Authentication Service Implementation
Implements IAuthService - core authentication operations (login, logout, register, etc.)
"""
import logging
from typing import Optional, Tuple, List
from datetime import datetime
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.interfaces.secondary.cache_service_interface import ICacheService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.services.filters.user_filter import UserFilter
from core.exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
    EmailAlreadyExistsException,
    ValidationException,
    InvalidTokenException,
    TokenExpiredException,
    DomainException,
    BusinessRuleException,
)
from .auth_service_base import AuthServiceBase

logger = logging.getLogger(__name__)


class AuthService(AuthServiceBase, IAuthService):
    """
    Service implementation for core authentication operations.
    
    Implements only IAuthService interface following Single Responsibility Principle.
    """
    
    def __init__(
        self,
        repository: IAppUserRepository,
        cache_service: ICacheService,
        settings_provider: ISettingsProvider,
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
            InvalidCredentialsException: If credentials are invalid (generic message for security)
        """
        user = await self.repository.find_by_email(email, client_id=client_id)
        if not user or user.client_id != client_id or not user.active:
            raise InvalidCredentialsException()
        
        if not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsException()
        
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
            InvalidTokenException: If token is invalid, revoked, or user is inactive
            UserNotFoundException: If user not found
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise InvalidTokenException()
        
        client_id_to_use = self._resolve_client_id_from_token(payload, client_id)
        if not client_id_to_use:
            raise InvalidTokenException()
        
        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidTokenException()
        
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        stored_user_id = await self.cache.get(cache_key)
        if not stored_user_id or stored_user_id != user_id:
            logger.warning("Refresh token not found in Redis or revoked", extra={"client_id": client_id_to_use})
            raise InvalidTokenException()
        
        user = await self.repository.find_by_id(user_id, client_id=client_id_to_use)
        if not user:
            raise UserNotFoundException(user_id=user_id)
        
        if not user.active:
            raise InvalidCredentialsException()
        
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
            InvalidCredentialsException: If credentials are invalid or user doesn't belong to client
        """
        try:
            user = await self._validate_login_credentials(email, password, client_id)
        except InvalidCredentialsException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True, extra={"email": email, "client_id": client_id})
            raise DomainException("Failed to authenticate user due to technical error", "AUTHENTICATION_FAILED")
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
        
        new_access_token, new_refresh_token = await self._generate_and_store_tokens(
            user_id, client_id_to_use
        )
        
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        await self.cache.delete(cache_key)
        
        logger.info("Token refresh successful", extra={"user_id": user_id, "client_id": client_id_to_use})
        return new_access_token, new_refresh_token
    
    async def _ensure_email_not_exists(self, email: str, client_id: str) -> None:
        """
        Ensure email doesn't already exist for the client.
        
        Raises:
            EmailAlreadyExistsException: If email already exists
        """
        existing = await self.repository.find_by_email(email, client_id=client_id)
        if existing:
            raise EmailAlreadyExistsException(email)
    
    def _validate_and_hash_password(self, password: str) -> str:
        """
        Validate password strength and hash it.
        
        Raises:
            ValueError: If password doesn't meet strength requirements
            
        Returns:
            Hashed password
        """
        self._validate_password_strength(password)
        return self._hash_password(password)
    
    def _create_user_domain_object(
        self, username: str, email: str, password_hash: str, name: str, client_id: str
    ) -> AppUser:
        """
        Create and validate user domain object.
        
        Args:
            username: Username
            email: User email
            password_hash: Hashed password
            name: User full name
            client_id: Client (tenant) ID
            
        Returns:
            Created and validated user domain object
        """
        user = AppUser(
            id=None,
            username=username,
            email=email,
            name=name,
            role=UserRole.USER,
            client_id=client_id,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            _password_hash=password_hash,  # Use protected field for encapsulation
        )
        user.validate()
        return user
    
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
            
        Raises:
            EmailAlreadyExistsException: If email already exists
            ValidationException: If validation fails
            DomainException: If technical error occurs
        """
        try:
            await self._ensure_email_not_exists(email, client_id)
            password_hash = self._validate_and_hash_password(password)
            user = self._create_user_domain_object(username, email, password_hash, name, client_id)
            
            created_user = await self.repository.save(user)
            logger.info("User registered successfully", extra={"user_id": created_user.id, "email": email, "client_id": client_id})
            return created_user
            
        except (EmailAlreadyExistsException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            # Unexpected error (database, network, etc.)
            logger.error(f"Unexpected error registering user: {e}", exc_info=True, extra={"email": email, "client_id": client_id})
            raise DomainException("Failed to register user due to technical error", "USER_REGISTRATION_FAILED")
    
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
            
        Raises:
            UserNotFoundException: If user not found
            InvalidCredentialsException: If current password is incorrect
            ValidationException: If new password doesn't meet requirements
            DomainException: If technical error occurs
        """
        try:
            user = await self.repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            if not self._verify_password(old_password, user.password_hash):
                raise InvalidCredentialsException()
            
            new_password_hash = self._validate_and_hash_password(new_password)
            user.change_password_hash(new_password_hash)  # Use controlled method for encapsulation
            user.updated_at = datetime.utcnow()
            
            await self.repository.save(user)
            
            logger.info("Password changed successfully", extra={"user_id": user_id, "client_id": user.client_id})
            return True
            
        except (UserNotFoundException, InvalidCredentialsException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            logger.error(f"Unexpected error changing password: {e}", exc_info=True, extra={"user_id": user_id, "client_id": client_id})
            raise DomainException("Failed to change password due to technical error", "PASSWORD_CHANGE_FAILED")
    
    async def get_current_user(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get current user by ID (multi-tenant).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for validation
        """
        return await self.repository.find_by_id(user_id, client_id=client_id)
    
    async def list_all_users(self, filter: Optional[UserFilter] = None) -> List[AppUser]:
        """
        List all users with optional filter (admin only).
        
        Filter Pattern: Service passes filter directly to repository.
        NO conditional logic here - repository handles all filtering, pagination, and sorting.
        
        Returns:
            List of users (empty list if error, graceful degradation)
        """
        logger.info("Listing users", extra={"filter": filter})
        
        try:
            result = await self.repository.find_all(filter)
            logger.info(f"Found {len(result)} users")
            return result
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True, extra={"filter": filter})
            # Graceful degradation: return empty list instead of failing
            return []
    
    async def count_users(self, filter: Optional[UserFilter] = None) -> int:
        """
        Counts users with optional filter.
        
        Filter Pattern: Uses same filter as list_all_users but without pagination/sorting.
        Simple delegation - repository handles all filter logic.
        
        Returns:
            Count of users (0 if error, graceful degradation)
        """
        logger.info("Counting users", extra={"filter": filter})
        
        try:
            result = await self.repository.count(filter)
            logger.info(f"Counted {result} users")
            return result
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}", exc_info=True, extra={"filter": filter})
            # Graceful degradation: return 0 instead of failing
            return 0
    
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
            
        Raises:
            BusinessRuleException: If trying to delete own account
            DomainException: If technical error occurs
        """
        try:
            if user_id == admin_id:
                raise BusinessRuleException("Cannot delete your own account", "CANNOT_DELETE_OWN_ACCOUNT")
            
            result = await self.repository.delete(user_id, client_id=client_id)
            if result:
                logger.info("User deleted successfully", extra={"user_id": user_id, "admin_id": admin_id, "client_id": client_id})
            return result
            
        except BusinessRuleException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting user: {e}", exc_info=True, extra={"user_id": user_id, "admin_id": admin_id, "client_id": client_id})
            raise DomainException("Failed to delete user due to technical error", "USER_DELETION_FAILED")

