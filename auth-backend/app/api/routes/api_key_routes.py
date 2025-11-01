"""
API Key Routes
Endpoints for Personal Access Token management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
import logging

from app.api.dtos.request.api_key_request import CreateApiKeyRequest
from app.api.dtos.response.api_key_response import (
    CreateApiKeyResponse,
    ApiKeyResponse,
    ListApiKeysResponse,
    RevokeApiKeyResponse
)
from app.api.middlewares.auth_middleware import get_current_user
from app.api.dicontainer.dicontainer import get_api_key_service
from core.domain.auth.app_user import AppUser
from core.domain.auth.api_key_scope import ApiKeyScope
from core.services.auth.api_key_service import ApiKeyService
from core.exceptions import BusinessRuleException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/api-keys", tags=["API Keys"])


@router.post("", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateApiKeyRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    api_key_service: Annotated[ApiKeyService, Depends(get_api_key_service)]
):
    """
    Create a new API key (Personal Access Token).
    
    The API key will be shown ONLY ONCE. Save it securely!
    
    API keys can be used for programmatic API access via X-API-Key header.
    """
    try:
        # Parse scopes
        scopes = [ApiKeyScope(scope) for scope in request.scopes]
        
        api_key, plain_key = await api_key_service.create_api_key(
            user_id=current_user.id,
            client_id=current_user.client_id,
            name=request.name,
            scopes=scopes,
            expires_in_days=request.expires_in_days
        )
        
        key_info = ApiKeyResponse(
            id=api_key.id,
            name=api_key.name,
            scopes=api_key.get_scopes_list(),
            last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            created_at=api_key.created_at.isoformat() if api_key.created_at else None,
            revoked_at=None,
            is_active=api_key.is_active()
        )
        
        return CreateApiKeyResponse(
            api_key=plain_key,
            key_info=key_info,
            message="API key created successfully. Save it now, it won't be shown again!"
        )
    except (BusinessRuleException, ValidationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating API key: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create API key")


@router.get("", response_model=ListApiKeysResponse)
async def list_api_keys(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    api_key_service: Annotated[ApiKeyService, Depends(get_api_key_service)]
):
    """
    List all API keys for current user.
    
    Includes both active and revoked keys.
    Does NOT include the actual key values (only metadata).
    """
    try:
        api_keys = await api_key_service.list_user_api_keys(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        keys_response = [
            ApiKeyResponse(
                id=key.id,
                name=key.name,
                scopes=key.get_scopes_list(),
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
                created_at=key.created_at.isoformat() if key.created_at else None,
                revoked_at=key.revoked_at.isoformat() if key.revoked_at else None,
                is_active=key.is_active()
            )
            for key in api_keys
        ]
        
        return ListApiKeysResponse(
            api_keys=keys_response,
            total=len(keys_response)
        )
    except Exception as e:
        logger.error(f"Error listing API keys: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list API keys")


@router.delete("/{key_id}", response_model=RevokeApiKeyResponse)
async def revoke_api_key(
    key_id: Annotated[str, Path(description="API key ID to revoke")],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    api_key_service: Annotated[ApiKeyService, Depends(get_api_key_service)]
):
    """
    Revoke an API key.
    
    Revoked keys cannot be used for authentication.
    This action cannot be undone.
    """
    try:
        success = await api_key_service.revoke_api_key(
            key_id=key_id,
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found or already revoked")
        
        return RevokeApiKeyResponse(
            success=True,
            message="API key revoked successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke API key")

