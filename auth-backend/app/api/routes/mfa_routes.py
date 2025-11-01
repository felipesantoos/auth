"""
MFA (Multi-Factor Authentication) Routes
Endpoints for 2FA/MFA management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import logging

from app.api.dtos.request.mfa_request import (
    EnableMFARequest,
    DisableMFARequest,
    RegenerateBackupCodesRequest
)
from app.api.dtos.response.mfa_response import (
    SetupMFAResponse,
    EnableMFAResponse,
    MFAStatusResponse,
    RegenerateBackupCodesResponse
)
from app.api.middlewares.auth_middleware import get_current_user
from app.api.dicontainer.dicontainer import get_mfa_service, get_auth_service
from core.domain.auth.app_user import AppUser
from core.services.auth.mfa_service import MFAService
from core.interfaces.primary.auth_service_interface import IAuthService
from core.exceptions import BusinessRuleException, InvalidCredentialsException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/mfa", tags=["MFA"])


@router.post("/setup", response_model=SetupMFAResponse)
async def setup_mfa(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    mfa_service: Annotated[MFAService, Depends(get_mfa_service)]
):
    """
    Setup MFA for user.
    
    Returns secret, QR code, and backup codes.
    User must verify TOTP code before MFA is enabled.
    """
    try:
        secret, qr_code, backup_codes = await mfa_service.setup_mfa(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return SetupMFAResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error setting up MFA: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to setup MFA")


@router.post("/enable", response_model=EnableMFAResponse)
async def enable_mfa(
    request: EnableMFARequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    mfa_service: Annotated[MFAService, Depends(get_mfa_service)]
):
    """
    Enable MFA after setup.
    
    Requires valid TOTP code verification.
    """
    try:
        await mfa_service.enable_mfa(
            user_id=current_user.id,
            client_id=current_user.client_id,
            secret=request.secret,
            totp_code=request.totp_code,
            backup_codes=request.backup_codes
        )
        
        return EnableMFAResponse(
            success=True,
            message="MFA enabled successfully"
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error enabling MFA: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enable MFA")


@router.post("/disable", response_model=EnableMFAResponse)
async def disable_mfa(
    request: DisableMFARequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    mfa_service: Annotated[MFAService, Depends(get_mfa_service)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)]
):
    """
    Disable MFA.
    
    Requires password confirmation for security.
    """
    try:
        # Verify password before disabling MFA (security measure)
        try:
            await auth_service.login(
                username=current_user.username,
                password=request.password,
                client_id=current_user.client_id
            )
        except InvalidCredentialsException:
            logger.warning(f"Invalid password attempt when disabling MFA for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Please provide your current password to disable MFA."
            )
        
        # Password verified, proceed to disable MFA
        await mfa_service.disable_mfa(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        logger.info(f"MFA disabled for user {current_user.id}")
        
        return EnableMFAResponse(
            success=True,
            message="MFA disabled successfully"
        )
    except HTTPException:
        raise
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error disabling MFA: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disable MFA")


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    mfa_service: Annotated[MFAService, Depends(get_mfa_service)]
):
    """Get MFA status for current user"""
    try:
        remaining_codes = await mfa_service.get_remaining_backup_codes_count(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return MFAStatusResponse(
            mfa_enabled=current_user.mfa_enabled,
            backup_codes_remaining=remaining_codes
        )
    except Exception as e:
        logger.error(f"Error getting MFA status: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get MFA status")


@router.post("/backup-codes/regenerate", response_model=RegenerateBackupCodesResponse)
async def regenerate_backup_codes(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    mfa_service: Annotated[MFAService, Depends(get_mfa_service)]
):
    """
    Regenerate backup codes.
    
    Invalidates all existing backup codes.
    """
    try:
        backup_codes = await mfa_service.regenerate_backup_codes(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return RegenerateBackupCodesResponse(
            backup_codes=backup_codes,
            message="Backup codes regenerated successfully. Save them now!"
        )
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to regenerate backup codes")

