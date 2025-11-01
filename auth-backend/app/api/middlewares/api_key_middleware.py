"""
API Key Authentication Middleware
Provides authentication via X-API-Key header for programmatic access
"""
from fastapi import Header, HTTPException, status
from typing import Optional, Annotated
import bcrypt
import logging

from core.domain.auth.app_user import AppUser
from core.domain.auth.api_key import ApiKey

logger = logging.getLogger(__name__)


async def get_current_user_from_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> Optional[AppUser]:
    """
    Authenticate user via API Key.
    
    This is an alternative to JWT authentication for programmatic access.
    
    Usage:
        Add X-API-Key header with value: ask_{64_hex_chars}
        
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        AppUser if API key is valid, None otherwise
        
    Note:
        This requires dependency injection to be fully functional.
        For now, returns None (use JWT auth).
    """
    if not x_api_key:
        return None
    
    # Validate format
    if not x_api_key.startswith("ask_"):
        logger.warning("Invalid API key format")
        return None
    
    # TODO: Inject ApiKeyService and UserRepository
    # api_key_service = get_api_key_service()
    # user_repository = get_user_repository()
    
    # validated_key = await api_key_service.validate_api_key(x_api_key)
    # if not validated_key or not validated_key.is_active():
    #     return None
    
    # user = await user_repository.find_by_id(
    #     validated_key.user_id,
    #     client_id=validated_key.client_id
    # )
    
    # return user
    
    logger.debug("API key auth not yet fully integrated - requires DI")
    return None


async def require_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> AppUser:
    """
    Require valid API key (raises exception if invalid).
    
    Use this as a dependency for routes that ONLY accept API key auth.
    
    Raises:
        HTTPException: 401 if API key is invalid or missing
    """
    user = await get_current_user_from_api_key(x_api_key)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return user


async def get_current_user_flexible(
    # Try JWT first
    authorization: Annotated[Optional[str], Header()] = None,
    # Then API key
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> AppUser:
    """
    Authenticate via JWT OR API key (flexible).
    
    Tries JWT first, then falls back to API key.
    Use this for routes that accept both authentication methods.
    
    Raises:
        HTTPException: 401 if both methods fail
    """
    # Try JWT first
    if authorization and authorization.startswith("Bearer "):
        # TODO: Use existing JWT auth
        # from app.api.middlewares.auth_middleware import get_current_user
        # return await get_current_user(authorization)
        pass
    
    # Try API key
    if x_api_key:
        user = await get_current_user_from_api_key(x_api_key)
        if user:
            return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (JWT or API key)",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )

