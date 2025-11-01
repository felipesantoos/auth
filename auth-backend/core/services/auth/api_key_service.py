"""
API Key Service Implementation
Handles creation and management of Personal Access Tokens for API authentication
"""
import logging
import bcrypt
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import uuid

from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope
from infra.database.repositories.api_key_repository import ApiKeyRepository
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import (
    BusinessRuleException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class ApiKeyService:
    """
    Service for API key (Personal Access Token) management.
    
    Features:
    - Create API keys with specific scopes
    - Validate API keys
    - Revoke API keys
    - List user's API keys
    """
    
    def __init__(
        self,
        repository: ApiKeyRepository,
        settings_provider: ISettingsProvider,
    ):
        self.repository = repository
        self.settings = settings_provider.get_settings()
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for storage"""
        return bcrypt.hashpw(key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_key(self, key: str, key_hash: str) -> bool:
        """Verify API key against hash"""
        try:
            return bcrypt.checkpw(key.encode('utf-8'), key_hash.encode('utf-8'))
        except Exception:
            return False
    
    async def create_api_key(
        self,
        user_id: str,
        client_id: str,
        name: str,
        scopes: List[ApiKeyScope],
        expires_in_days: Optional[int] = None
    ) -> Tuple[ApiKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            client_id: Client ID
            name: Human-readable name for the key
            scopes: List of permission scopes
            expires_in_days: Optional expiration (defaults to setting)
            
        Returns:
            Tuple of (ApiKey object, plain text key)
            The plain text key is only shown once!
            
        Raises:
            BusinessRuleException: If user has too many keys
            ValidationException: If invalid scopes
        """
        try:
            # Check key limit
            count = await self.repository.count_by_user(user_id, client_id)
            if count >= self.settings.api_key_max_per_user:
                raise BusinessRuleException(
                    f"Maximum API keys limit reached ({self.settings.api_key_max_per_user})",
                    "API_KEY_LIMIT_REACHED"
                )
            
            # Validate scopes
            if not scopes or len(scopes) == 0:
                raise ValidationException("At least one scope is required")
            
            # Generate API key
            plain_key = ApiKey.generate_key()
            key_hash = self._hash_key(plain_key)
            
            # Calculate expiration
            expires_at = None
            if expires_in_days is None:
                expires_in_days = self.settings.api_key_default_expire_days
            
            if expires_in_days > 0:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create API key
            api_key = ApiKey(
                id=str(uuid.uuid4()),
                user_id=user_id,
                client_id=client_id,
                name=name,
                key_hash=key_hash,
                scopes=scopes,
                last_used_at=None,
                expires_at=expires_at,
                created_at=datetime.utcnow(),
                revoked_at=None
            )
            
            api_key.validate()
            saved_key = await self.repository.save(api_key)
            
            logger.info(f"API key created for user {user_id}: {name}")
            return saved_key, plain_key
            
        except (BusinessRuleException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Error creating API key: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to create API key",
                "API_KEY_CREATION_FAILED"
            )
    
    async def validate_api_key(
        self,
        plain_key: str
    ) -> Optional[ApiKey]:
        """
        Validate an API key and return if valid.
        
        Args:
            plain_key: Plain text API key
            
        Returns:
            ApiKey object if valid, None otherwise
        """
        try:
            # Extract hash from key for lookup
            # In production, you might want to add an index
            # For now, we'll need to iterate (not ideal for production)
            
            # This is a simplified implementation
            # In production, consider storing a hash prefix for faster lookup
            
            # For now, return None and log
            # A proper implementation would:
            # 1. Hash the key
            # 2. Look up by hash in database
            # 3. Verify not expired/revoked
            # 4. Update last_used_at
            
            logger.warning("validate_api_key needs hash-based lookup implementation")
            return None
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}", exc_info=True)
            return None
    
    async def validate_api_key_by_hash(
        self,
        key_hash: str
    ) -> Optional[ApiKey]:
        """
        Validate API key by hash (for internal use).
        
        Args:
            key_hash: Hashed API key
            
        Returns:
            ApiKey object if valid, None otherwise
        """
        try:
            api_key = await self.repository.find_by_key_hash(key_hash)
            
            if not api_key:
                return None
            
            if not api_key.is_active():
                logger.warning(f"Inactive API key used: {api_key.id}")
                return None
            
            # Update last used
            api_key.update_last_used()
            await self.repository.save(api_key)
            
            return api_key
            
        except Exception as e:
            logger.error(f"Error validating API key by hash: {e}", exc_info=True)
            return None
    
    async def revoke_api_key(
        self,
        key_id: str,
        user_id: str,
        client_id: str
    ) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: API key ID
            user_id: User ID (for authorization)
            client_id: Client ID
            
        Returns:
            True if revoked successfully
        """
        try:
            api_key = await self.repository.find_by_id(key_id)
            
            if not api_key:
                logger.warning(f"API key not found: {key_id}")
                return False
            
            # Authorization: only owner can revoke
            if api_key.user_id != user_id or api_key.client_id != client_id:
                logger.warning(f"Unauthorized API key revoke attempt: {key_id}")
                return False
            
            if api_key.is_revoked():
                return True  # Already revoked
            
            api_key.revoke()
            await self.repository.save(api_key)
            
            logger.info(f"API key revoked: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking API key: {e}", exc_info=True)
            return False
    
    async def list_user_api_keys(
        self,
        user_id: str,
        client_id: str
    ) -> List[ApiKey]:
        """
        List all API keys for a user (includes revoked).
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            List of API keys
        """
        try:
            return await self.repository.find_by_user(user_id, client_id)
        except Exception as e:
            logger.error(f"Error listing API keys: {e}", exc_info=True)
            return []
    
    async def list_active_api_keys(
        self,
        user_id: str,
        client_id: str
    ) -> List[ApiKey]:
        """
        List active API keys for a user.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            List of active API keys
        """
        try:
            return await self.repository.find_active_by_user(user_id, client_id)
        except Exception as e:
            logger.error(f"Error listing active API keys: {e}", exc_info=True)
            return []

