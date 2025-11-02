"""
Passwordless Authentication Routes
Endpoints for magic link authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Annotated
import logging

from app.api.dtos.request.passwordless_request import (
    SendMagicLinkRequest,
    VerifyMagicLinkRequest
)
from app.api.dtos.response.passwordless_response import (
    SendMagicLinkResponse,
    VerifyMagicLinkResponse
)
from app.api.dicontainer.dicontainer import get_passwordless_service, get_auth_service
from app.api.middlewares.rate_limit_middleware import limiter
from core.services.auth.passwordless_service import PasswordlessService
from core.interfaces.primary.auth_service_interface import IAuthService
from core.exceptions import InvalidTokenException, TokenExpiredException, UserNotFoundException, BusinessRuleException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/passwordless", tags=["Passwordless Auth"])


@router.post("/send", response_model=SendMagicLinkResponse)
@limiter.limit("3/hour")  # Limit to 3 magic links per hour per IP
async def send_magic_link(
    magic_link_request: SendMagicLinkRequest,
    request: Request,
    passwordless_service: Annotated[PasswordlessService, Depends(get_passwordless_service)]
):
    """
    Send magic link for passwordless login.
    
    User will receive an email with a login link.
    Link expires in 15 minutes.
    
    Rate limited to 3 requests per hour to prevent abuse.
    """
    try:
        await passwordless_service.send_magic_link(
            email=magic_link_request.email,
            client_id=magic_link_request.client_id
        )
        
        return SendMagicLinkResponse(
            success=True,
            message="Magic link sent to your email. Check your inbox!"
        )
    except UserNotFoundException:
        # For security, don't reveal if email exists or not
        return SendMagicLinkResponse(
            success=True,
            message="If the email exists, a magic link has been sent."
        )
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error sending magic link: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send magic link")


@router.post("/verify", response_model=VerifyMagicLinkResponse)
async def verify_magic_link(
    request: VerifyMagicLinkRequest,
    passwordless_service: Annotated[PasswordlessService, Depends(get_passwordless_service)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)]
):
    """
    Verify magic link and login.
    
    Returns access token and refresh token on success.
    Magic links are single-use only.
    """
    try:
        # Verify magic link and get user
        user = await passwordless_service.verify_magic_link(
            user_id=request.user_id,
            token=request.token,
            client_id=request.client_id
        )
        
        # Generate tokens (reuse existing auth service logic)
        from core.services.auth.auth_service import AuthService
        if isinstance(auth_service, AuthService):
            access_token, refresh_token = await auth_service._generate_and_store_tokens(
                user.id, request.client_id
            )
        else:
            raise HTTPException(status_code=500, detail="Auth service not available")
        
        return VerifyMagicLinkResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value
            }
        )
    except (InvalidTokenException, TokenExpiredException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error verifying magic link: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify magic link")

