"""
OAuth Service Implementation
Implements IOAuthService - OAuth2 authentication operations
"""
import logging
import uuid
from typing import Optional, Tuple
from datetime import datetime
from core.interfaces.primary.oauth_service_interface import IOAuthService
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.interfaces.secondary.cache_service_interface import CacheServiceInterface
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.exceptions import (
    ValidationException,
    MissingRequiredFieldException,
    InvalidCredentialsException,
    DomainException,
)
from .auth_service_base import AuthServiceBase

logger = logging.getLogger(__name__)


class OAuthService(AuthServiceBase, IOAuthService):
    """
    Service implementation for OAuth2 authentication operations.
    
    Implements only IOAuthService interface following Single Responsibility Principle.
    """
    
    def __init__(
        self,
        repository: AppUserRepositoryInterface,
        cache_service: CacheServiceInterface,
        settings_provider: SettingsProviderInterface,
    ):
        """
        Constructor for OAuthService.
        
        Args:
            repository: Repository interface for user operations
            cache_service: Cache service interface
            settings_provider: Settings provider interface
        """
        super().__init__(cache_service, settings_provider)
        self.repository = repository
    
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
            username = email.split('@')[0]  # Use email prefix as username
            random_password = str(uuid.uuid4())
            password_hash = self._hash_password(random_password)
            
            user = AppUser(
                id=None,
                username=username,
                email=email,
                name=name,
                role=UserRole.USER,
                client_id=client_id,
                active=True,
                _password_hash=password_hash,  # Use protected field for encapsulation
            )
            user.validate()
            user = await self.repository.save(user)
            logger.info("New user created via OAuth", extra={"user_id": user.id, "provider": provider, "client_id": client_id})
        else:
            if user.name != name:
                user.name = name
                user.updated_at = datetime.utcnow()
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
            
        Raises:
            MissingRequiredFieldException: If client_id is missing
            InvalidCredentialsException: If user account is deactivated
            ValidationException: If validation fails
            DomainException: If technical error occurs
        """
        if not client_id:
            raise MissingRequiredFieldException("client_id")
        
        logger.info("OAuth login attempt", extra={"provider": provider, "email": email, "client_id": client_id})
        
        try:
            user = await self._create_or_update_oauth_user(email, name, client_id, provider)
            
            if not user.active:
                raise InvalidCredentialsException()
            
            access_token, refresh_token = await self._generate_and_store_tokens(user.id, client_id)
            logger.info("OAuth login successful", extra={"user_id": user.id, "provider": provider, "client_id": client_id})
            return access_token, refresh_token, user
            
        except (MissingRequiredFieldException, InvalidCredentialsException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OAuth login: {e}", exc_info=True, extra={"provider": provider, "email": email, "client_id": client_id})
            raise DomainException("Failed to authenticate via OAuth due to technical error", "OAUTH_AUTHENTICATION_FAILED")

