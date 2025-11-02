"""
Email Verification Routes
Endpoints for email verification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import logging

from app.api.dtos.request.email_verification_request import (
    VerifyEmailRequest,
    ResendVerificationRequest
)
from app.api.dtos.response.email_verification_response import (
    VerifyEmailResponse,
    ResendVerificationResponse,
    EmailVerificationStatusResponse
)
from app.api.middlewares.auth_middleware import get_current_user
from app.api.dicontainer.dicontainer import get_email_verification_service
from core.domain.auth.app_user import AppUser
from core.services.auth.email_verification_service import EmailVerificationService
from core.exceptions import InvalidTokenException, TokenExpiredException, UserNotFoundException, BusinessRuleException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/email", tags=["Email Verification"])


@router.post("/verify", response_model=VerifyEmailResponse)
async def verify_email(
    verify_request: VerifyEmailRequest,
    email_verification_service: Annotated[EmailVerificationService, Depends(get_email_verification_service)]
):
    """
    Verify email address with token.
    
    Token is sent via email after registration.
    Client ID can come from body or X-Client-ID header.
    """
    try:
        # Use client_id from body, or require from header/context
        client_id = verify_request.client_id
        if not client_id:
            # In production, get from header or raise error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id required (in body or X-Client-ID header)"
            )
        
        await email_verification_service.verify_email(
            user_id=verify_request.user_id,
            token=verify_request.token,
            client_id=client_id
        )
        
        return VerifyEmailResponse(
            success=True,
            message="Email verified successfully"
        )
    except (InvalidTokenException, TokenExpiredException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        logger.error(f"Error verifying email: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify email")


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    email_verification_service: Annotated[EmailVerificationService, Depends(get_email_verification_service)]
):
    """
    Resend verification email.
    
    Can only be called if email is not yet verified.
    """
    try:
        await email_verification_service.resend_verification_email(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return ResendVerificationResponse(
            success=True,
            message="Verification email sent. Please check your inbox."
        )
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error resending verification: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")


@router.get("/status", response_model=EmailVerificationStatusResponse)
async def get_verification_status(
    current_user: Annotated[AppUser, Depends(get_current_user)],
):
    """
    Check if current user's email is verified.
    """
    return EmailVerificationStatusResponse(
        email_verified=current_user.email_verified
    )

