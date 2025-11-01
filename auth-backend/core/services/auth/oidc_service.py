"""
OIDC Service Implementation
Handles OpenID Connect authentication
"""
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import secrets

from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.interfaces.secondary.cache_service_interface import ICacheService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import (
    BusinessRuleException,
    ValidationException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


class OIDCService:
    """
    Service for OpenID Connect (OIDC) authentication.
    
    OIDC is built on top of OAuth 2.0 and provides:
    - Standard authentication flow
    - ID tokens (JWT)
    - UserInfo endpoint
    
    Compatible with providers like:
    - Google
    - Microsoft Azure AD
    - Okta
    - Auth0
    - Keycloak
    """
    
    def __init__(
        self,
        user_repository: IAppUserRepository,
        cache_service: ICacheService,
        settings_provider: ISettingsProvider,
    ):
        self.user_repository = user_repository
        self.cache_service = cache_service
        self.settings = settings_provider.get_settings()
    
    def is_enabled(self) -> bool:
        """Check if OIDC is enabled"""
        return self.settings.oidc_enabled
    
    async def get_authorization_url(
        self,
        client_id: str,
        state: Optional[str] = None
    ) -> str:
        """
        Get OIDC authorization URL (redirect to provider).
        
        Args:
            client_id: Client ID
            state: Optional state parameter (CSRF protection)
            
        Returns:
            Authorization URL
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "OIDC is not enabled",
                "OIDC_NOT_ENABLED"
            )
        
        try:
            # In production, use authlib:
            # from authlib.integrations.base_client import OAuthError
            # from authlib.integrations.httpx_client import AsyncOAuth2Client
            
            # client = AsyncOAuth2Client(
            #     client_id=self.settings.oidc_client_id,
            #     client_secret=self.settings.oidc_client_secret
            # )
            # authorization_url, state = client.create_authorization_url(
            #     self.settings.oidc_issuer + '/authorize',
            #     redirect_uri=self.settings.oidc_redirect_uri,
            #     scope='openid profile email'
            # )
            # return authorization_url
            
            # Generate secure state for CSRF protection
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Store state in Redis for validation (10 min TTL)
            import json
            import base64
            state_data = {"client_id": client_id}
            encoded_state = base64.b64encode(json.dumps(state_data).encode()).decode()
            
            await self.cache_service.store_state(
                key=f"oidc:state:{encoded_state}",
                state=state_data,
                ttl=600  # 10 minutes
            )
            
            issuer = self.settings.oidc_issuer or "https://accounts.google.com"
            redirect_uri = self.settings.oidc_redirect_uri or f"{self.settings.api_base_url}/auth/oidc/callback"
            
            authorization_url = (
                f"{issuer}/authorize"
                f"?client_id={self.settings.oidc_client_id}"
                f"&redirect_uri={redirect_uri}"
                f"&response_type=code"
                f"&scope=openid profile email"
                f"&state={encoded_state}"
            )
            
            logger.info(f"OIDC login initiated for client {client_id}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error getting OIDC authorization URL: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to initiate OIDC login",
                "OIDC_LOGIN_FAILED"
            )
    
    async def handle_callback(
        self,
        code: str,
        state: str,
        client_id: str
    ) -> AppUser:
        """
        Handle OIDC callback (exchange code for tokens and get user info).
        
        Args:
            code: Authorization code
            state: State parameter (validate against stored state)
            client_id: Client ID
            
        Returns:
            Authenticated user (created if doesn't exist)
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "OIDC is not enabled",
                "OIDC_NOT_ENABLED"
            )
        
        try:
            # Validate state (CSRF protection)
            state_key = f"oidc:state:{state}"
            stored_state = await self.cache_service.get(state_key)
            
            if not stored_state:
                logger.warning(f"OIDC state not found or expired: {state}")
                raise BusinessRuleException(
                    "Invalid or expired OIDC state (possible CSRF attack)",
                    "OIDC_INVALID_STATE"
                )
            
            # Delete state to prevent replay attacks (single-use)
            await self.cache_service.delete(state_key)
            
            # In production, use authlib:
            # from authlib.integrations.httpx_client import AsyncOAuth2Client
            
            # client = AsyncOAuth2Client(...)
            # token = await client.fetch_token(
            #     token_url,
            #     code=code,
            #     redirect_uri=self.settings.oidc_redirect_uri
            # )
            # userinfo = await client.userinfo(token=token['access_token'])
            
            # email = userinfo['email']
            # name = userinfo['name']
            # username = userinfo.get('preferred_username') or email.split('@')[0]
            
            # Simplified implementation (placeholder)
            email = "oidc_user@example.com"  # Extract from userinfo
            name = "OIDC User"  # Extract from userinfo
            username = email.split('@')[0]
            
            # Find or create user
            user = await self.user_repository.find_by_email(email, client_id=client_id)
            
            if not user:
                # Auto-provision user from OIDC userinfo
                user = AppUser(
                    id=None,
                    username=username,
                    email=email,
                    name=name,
                    role=UserRole.USER,
                    client_id=client_id,
                    active=True,
                    email_verified=True,  # Auto-verified for OIDC users
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    _password_hash="oidc_user_no_password"
                )
                
                user.validate()
                user = await self.user_repository.save(user)
                
                logger.info(f"OIDC user auto-provisioned: {email}")
            
            logger.info(f"OIDC authentication successful for {email}")
            return user
            
        except (BusinessRuleException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Error handling OIDC callback: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to process OIDC callback",
                "OIDC_CALLBACK_FAILED"
            )
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get OIDC configuration.
        
        Returns:
            OIDC configuration dict
        """
        if not self.is_enabled():
            return {"enabled": False}
        
        return {
            "enabled": True,
            "issuer": self.settings.oidc_issuer,
            "client_id": self.settings.oidc_client_id,
            "redirect_uri": self.settings.oidc_redirect_uri,
        }

