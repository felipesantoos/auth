"""
OAuth Service Implementation
Implements IOAuthService - OAuth2 authentication operations
"""
import logging
import uuid
from typing import Optional, Tuple
from datetime import datetime
from core.interfaces.primary.oauth_service_interface import IOAuthService
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.interfaces.secondary.cache_service_interface import ICacheService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.domain.auth.app_user import AppUser
# REMOVED: from core.domain.auth.user_role import UserRole (roles now in WorkspaceMember)
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
        repository: IAppUserRepository,
        cache_service: ICacheService,
        settings_provider: ISettingsProvider,
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
        self, email: str, name: str, provider: str
    ) -> Tuple[AppUser, Optional[str]]:
        """
        Create new OAuth user or update existing user's name (multi-workspace).
        
        OAuth users get a random password since they authenticate via provider.
        If user exists, we update their name in case it changed on the OAuth provider.
        Creates personal workspace automatically for new users.
        
        Args:
            email: User email from OAuth provider
            name: User name from OAuth provider
            provider: OAuth provider name (for logging)
            
        Returns:
            Tuple of (user object, workspace_id)
        """
        user = await self.repository.find_by_email(email)
        workspace_id = None
        
        if not user:
            # Create new OAuth user with random password (never used for auth)
            username = email.split('@')[0]  # Use email prefix as username
            
            # Make username unique by adding random suffix if needed
            base_username = username
            counter = 1
            while await self._username_exists(username):
                username = f"{base_username}{counter}"
                counter += 1
            
            random_password = str(uuid.uuid4())
            password_hash = self._hash_password(random_password)
            
            user = AppUser(
                id=None,
                username=username,
                email=email,
                name=name,
                # REMOVED: role (now in WorkspaceMember)
                # REMOVED: client_id (now via workspace_member)
                active=True,
                _password_hash=password_hash,
                email_verified=True,  # OAuth emails are pre-verified
            )
            user.validate()
            user = await self.repository.save(user)
            
            # Create personal workspace (if services available)
            if self.workspace_service and self.workspace_member_service:
                try:
                    from core.domain.workspace.workspace_role import WorkspaceRole
                    
                    workspace = await self.workspace_service.create_workspace(
                        name=f"{name}'s Workspace",
                        description=f"Personal workspace for {name} (created via {provider})"
                    )
                    workspace_id = workspace.id
                    
                    await self.workspace_member_service.add_member(
                        user_id=user.id,
                        workspace_id=workspace.id,
                        role=WorkspaceRole.ADMIN
                    )
                    
                    logger.info(
                        "New user created via OAuth with workspace",
                        extra={
                            "user_id": user.id,
                            "provider": provider,
                            "workspace_id": workspace_id
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to create workspace for OAuth user: {e}", exc_info=True)
            else:
                logger.info("New user created via OAuth", extra={"user_id": user.id, "provider": provider})
        else:
            # Update existing user
            if user.name != name:
                user.name = name
                user.updated_at = datetime.utcnow()
                user = await self.repository.save(user)
            
            # Get user's first workspace for context
            if self.workspace_member_service:
                try:
                    workspaces = await self.workspace_member_service.get_user_workspaces(user.id)
                    if workspaces:
                        workspace_id = workspaces[0].workspace_id
                except Exception as e:
                    logger.warning(f"Could not fetch user workspaces: {e}")
            
            logger.info("Existing user logged in via OAuth", extra={"user_id": user.id, "provider": provider})
        
        return user, workspace_id
    
    async def _username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        try:
            # This would need a find_by_username method in repository
            # For now, return False (username uniqueness handled by DB constraint)
            return False
        except Exception:
            return False
    
    async def oauth_login(
        self,
        provider: str,
        email: str,
        name: str,
        oauth_id: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> Tuple[str, str, AppUser]:
        """
        Login or register user via OAuth2 (multi-workspace architecture).
        
        Creates user if doesn't exist (with personal workspace), or logs in existing user.
        
        Args:
            provider: OAuth provider name (e.g., 'google', 'github')
            email: User email from OAuth provider
            name: User name from OAuth provider
            oauth_id: Optional OAuth provider user ID
            client_id: Optional client ID (deprecated, for backwards compatibility)
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            InvalidCredentialsException: If user account is deactivated
            ValidationException: If validation fails
            DomainException: If technical error occurs
        """
        logger.info("OAuth login attempt", extra={"provider": provider, "email": email})
        
        try:
            user, workspace_id = await self._create_or_update_oauth_user(email, name, provider)
            
            if not user.active:
                raise InvalidCredentialsException()
            
            # Use workspace_id if available, otherwise client_id (backwards compat), or default
            effective_client_id = workspace_id or client_id or "oauth-default"
            
            access_token, refresh_token = await self._generate_and_store_tokens(user.id, effective_client_id)
            logger.info(
                "OAuth login successful",
                extra={
                    "user_id": user.id,
                    "provider": provider,
                    "workspace_id": workspace_id
                }
            )
            return access_token, refresh_token, user
            
        except (InvalidCredentialsException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OAuth login: {e}", exc_info=True, extra={"provider": provider, "email": email})
            raise DomainException("Failed to authenticate via OAuth due to technical error", "OAUTH_AUTHENTICATION_FAILED")

