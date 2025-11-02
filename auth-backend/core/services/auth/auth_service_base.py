"""
Base class for authentication services
Contains shared utility methods for password hashing, token generation, etc.
"""
import logging
import re
from typing import Optional
from datetime import datetime, timedelta
import bcrypt
import jwt
from core.interfaces.secondary.cache_service_interface import ICacheService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import InvalidPasswordException

logger = logging.getLogger(__name__)


class AuthServiceBase:
    """
    Base class with shared utility methods for authentication services.
    
    This class provides common functionality that multiple auth services need,
    such as password hashing, token generation, and validation.
    """
    
    def __init__(
        self,
        cache_service: ICacheService,
        settings_provider: ISettingsProvider,
    ):
        """
        Constructor for base auth service.
        
        Args:
            cache_service: Cache service interface
            settings_provider: Settings provider interface
        """
        self.cache = cache_service
        self.settings = settings_provider
    
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
            InvalidPasswordException: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise InvalidPasswordException("Password must be at least 8 characters")
        
        if not re.search(r'[A-Z]', password):
            raise InvalidPasswordException("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise InvalidPasswordException("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password):
            raise InvalidPasswordException("Password must contain at least one number")
    
    def _generate_token(self, user_id: str, token_type: str, client_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """
        Generate JWT token with client_id and session_id in payload (multi-tenant).
        
        Args:
            user_id: User ID
            token_type: Token type ("access" or "refresh")
            client_id: Client (tenant) ID
            session_id: Session ID (for tracking active sessions)
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
        
        # Include session_id for session management (only in access tokens)
        if session_id and token_type == "access":
            payload["session_id"] = session_id
        
        return jwt.encode(
            payload,
            self.settings.get_jwt_secret(),
            algorithm=self.settings.get_jwt_algorithm()
        )
    
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
        self, user_id: str, client_id: str, session_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Generate both access and refresh tokens, and store refresh token.
        
        We generate both tokens together to ensure they're consistent (same client_id),
        and store only the refresh token in Redis to enable revocation.
        
        Args:
            user_id: User ID
            client_id: Client (tenant) ID
            session_id: Session ID (for tracking active sessions)
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        access_token = self._generate_token(user_id, "access", client_id, session_id)
        refresh_token = self._generate_token(user_id, "refresh", client_id, session_id)
        await self._generate_and_store_refresh_token(user_id, refresh_token, client_id)
        return access_token, refresh_token
    
    def generate_access_token_with_session(self, user_id: str, client_id: str, session_id: str) -> str:
        """
        Generate a new access token with session_id.
        
        Used to regenerate access token after session creation.
        
        Args:
            user_id: User ID
            client_id: Client ID
            session_id: Session ID
            
        Returns:
            New access token with session_id
        """
        return self._generate_token(user_id, "access", client_id, session_id)

