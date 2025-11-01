"""
WebAuthn Routes
Endpoints for biometric authentication (Passkeys, Face ID, Touch ID)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
import logging

from app.api.middlewares.auth_middleware import get_current_user
from app.api.dicontainer.dicontainer import get_webauthn_service, get_auth_service
from core.domain.auth.app_user import AppUser
from core.services.auth.webauthn_service import WebAuthnService
from core.interfaces.primary.auth_service_interface import IAuthService
from core.exceptions import BusinessRuleException, UserNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/webauthn", tags=["WebAuthn"])


@router.post("/register/begin")
async def register_begin(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    webauthn_service: Annotated[WebAuthnService, Depends(get_webauthn_service)]
):
    """
    Begin WebAuthn credential registration (get challenge).
    
    Returns registration options for client-side WebAuthn API.
    """
    try:
        options = await webauthn_service.register_begin(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        return options
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error beginning WebAuthn registration: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to begin WebAuthn registration")


@router.post("/register/complete")
async def register_complete(
    credential_id: str,
    public_key: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    webauthn_service: Annotated[WebAuthnService, Depends(get_webauthn_service)],
    device_name: str = None
):
    """
    Complete WebAuthn credential registration (store credential).
    
    Called after user completes biometric verification on device.
    """
    try:
        credential = await webauthn_service.register_complete(
            user_id=current_user.id,
            client_id=current_user.client_id,
            credential_id=credential_id,
            public_key=public_key,
            device_name=device_name
        )
        
        return {
            "success": True,
            "credential_id": credential.id,
            "device_name": credential.get_device_description(),
            "message": "WebAuthn credential registered successfully"
        }
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error completing WebAuthn registration: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete WebAuthn registration")


@router.post("/authenticate/begin")
async def authenticate_begin(
    user_id: str,
    client_id: str,
    webauthn_service: Annotated[WebAuthnService, Depends(get_webauthn_service)]
):
    """
    Begin WebAuthn authentication (get challenge).
    
    Returns authentication options for client-side WebAuthn API.
    """
    try:
        options = await webauthn_service.authenticate_begin(
            user_id=user_id,
            client_id=client_id
        )
        return options
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error beginning WebAuthn authentication: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to begin WebAuthn authentication")


@router.post("/authenticate/complete")
async def authenticate_complete(
    user_id: str,
    client_id: str,
    credential_id: str,
    authenticator_data: str,
    signature: str,
    client_data_json: str,
    webauthn_service: Annotated[WebAuthnService, Depends(get_webauthn_service)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)]
):
    """
    Complete WebAuthn authentication (verify signature).
    
    Returns access token on success.
    """
    try:
        user = await webauthn_service.authenticate_complete(
            user_id=user_id,
            client_id=client_id,
            credential_id=credential_id,
            authenticator_data=authenticator_data,
            signature=signature,
            client_data_json=client_data_json
        )
        
        # Generate JWT tokens
        from core.services.auth.auth_service import AuthService
        if isinstance(auth_service, AuthService):
            access_token, refresh_token = await auth_service._generate_and_store_tokens(
                user.id, client_id
            )
        else:
            raise HTTPException(status_code=500, detail="Auth service not available")
        
        return {
            "success": True,
            "message": "WebAuthn authentication successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value
            }
        }
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error completing WebAuthn authentication: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete WebAuthn authentication")


@router.get("/credentials")
async def list_credentials(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    webauthn_service: Annotated[WebAuthnService, Depends(get_webauthn_service)]
):
    """List all WebAuthn credentials for current user"""
    try:
        credentials = await webauthn_service.list_credentials(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return {
            "credentials": [
                {
                    "id": cred.id,
                    "device_name": cred.get_device_description(),
                    "created_at": cred.created_at.isoformat() if cred.created_at else None,
                    "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
                    "is_active": cred.is_active()
                }
                for cred in credentials
            ],
            "total": len(credentials)
        }
    except Exception as e:
        logger.error(f"Error listing WebAuthn credentials: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list credentials")


@router.delete("/credentials/{credential_id}")
async def revoke_credential(
    credential_id: Annotated[str, Path(description="Credential ID to revoke")],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    webauthn_service: Annotated[WebAuthnService, Depends(get_webauthn_service)]
):
    """Revoke a WebAuthn credential"""
    try:
        success = await webauthn_service.revoke_credential(
            credential_id=credential_id,
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found or already revoked")
        
        return {
            "success": True,
            "message": "WebAuthn credential revoked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking WebAuthn credential: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke credential")

