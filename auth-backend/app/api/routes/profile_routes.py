"""
User Profile Routes
Self-service profile management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Annotated
import logging

from app.api.middlewares.auth_middleware import get_current_user
from app.api.dicontainer.dicontainer import get_user_profile_service
from core.domain.auth.app_user import AppUser
from core.services.auth.user_profile_service import UserProfileService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/profile", tags=["User Profile"])


# DTOs
class ProfileResponse(BaseModel):
    """User profile response"""
    id: str
    username: str
    email: str
    name: str
    role: str
    email_verified: bool
    mfa_enabled: bool
    created_at: str


class UpdateProfileRequest(BaseModel):
    """Update profile request"""
    name: str = None
    username: str = None


class ChangeEmailRequest(BaseModel):
    """Change email request"""
    new_email: str
    password: str


class DeleteAccountRequest(BaseModel):
    """Delete account request"""
    password: str


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_user: Annotated[AppUser, Depends(get_current_user)]):
    """
    Get current user profile.
    
    Returns detailed information about the currently authenticated user.
    """
    return ProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        email_verified=current_user.email_verified,
        mfa_enabled=current_user.mfa_enabled,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )


@router.put("/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)]
):
    """
    Update profile (name, username).
    
    Allows users to update their own profile information.
    Username must be unique within the client.
    """
    try:
        updated = await profile_service.update_profile(
            user_id=current_user.id,
            client_id=current_user.client_id,
            name=request.name,
            username=request.username
        )
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated.id,
                "username": updated.username,
                "name": updated.name
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/change-email")
async def request_email_change(
    request: ChangeEmailRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)]
):
    """
    Request email change (requires verification).
    
    Initiates email change process. Requires current password for security.
    A verification email will be sent to the new address.
    """
    try:
        result = await profile_service.request_email_change(
            user_id=current_user.id,
            new_email=request.new_email,
            password=request.password
        )
        
        return {"message": result}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error requesting email change: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process email change request"
        )


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)]
):
    """
    Delete account (soft delete - requires password).
    
    Permanently deactivates the user account. This action cannot be undone.
    Requires password confirmation for security.
    All active sessions and tokens will be revoked.
    """
    try:
        await profile_service.delete_account(
            user_id=current_user.id,
            password=request.password
        )
        
        return {"message": "Account deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.post("/avatar", status_code=status.HTTP_200_OK)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: Annotated[AppUser, Depends(get_current_user)],
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)]
):
    """
    Upload user avatar.
    
    Accepts image files (JPEG, PNG, GIF, WebP).
    Image will be automatically optimized and resized.
    """
    try:
        avatar_url = await profile_service.update_avatar(
            user_id=current_user.id,
            client_id=current_user.client_id,
            avatar_file=avatar
        )
        
        return {"avatar_url": avatar_url, "message": "Avatar uploaded successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar"
        )


@router.delete("/avatar", status_code=status.HTTP_200_OK)
async def delete_avatar(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)]
):
    """Delete user avatar."""
    try:
        await profile_service.delete_avatar(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return {"message": "Avatar deleted successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting avatar: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete avatar"
        )


# KYC Endpoints
class KYCStatusResponse(BaseModel):
    """KYC status response"""
    kyc_status: str
    kyc_verified: bool
    kyc_pending: bool
    kyc_verified_at: str = None


@router.post("/kyc/document", status_code=status.HTTP_201_CREATED)
async def submit_kyc_document(
    document: UploadFile = File(...),
    current_user: Annotated[AppUser, Depends(get_current_user)] = None,
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)] = None
):
    """
    Submit KYC document for verification.
    
    - **document**: Identity document (passport, ID card, driver's license)
    - Accepted formats: PDF, JPG, PNG
    - Max size: 10MB
    """
    try:
        result = await profile_service.submit_kyc_document(
            user_id=current_user.id,
            client_id=current_user.client_id,
            document_file=document
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting KYC document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit KYC document"
        )


@router.get("/kyc/status", response_model=KYCStatusResponse)
async def get_kyc_status(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    profile_service: Annotated[UserProfileService, Depends(get_user_profile_service)]
):
    """Get KYC verification status."""
    try:
        status_info = await profile_service.get_kyc_status(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        return status_info
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting KYC status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get KYC status"
        )

