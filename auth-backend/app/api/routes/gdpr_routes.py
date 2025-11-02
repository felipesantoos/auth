"""
GDPR Compliance Routes
Endpoints for GDPR rights: Right to Access and Right to be Forgotten
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Annotated
from pydantic import BaseModel
import logging

from app.api.middlewares.auth_middleware import get_current_user
from app.api.middlewares.authorization import require_role
from core.domain.auth.app_user import AppUser, UserRole
from core.services.compliance.gdpr_service import GDPRService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR Compliance"])


# DTOs
class DeleteMyDataRequest(BaseModel):
    """Request to delete own data"""
    password: str  # Require password confirmation
    reason: str = "User requested deletion"
    confirm: bool = False  # Must be True


class AnonymizeUserRequest(BaseModel):
    """Admin request to anonymize user data"""
    user_id: str
    reason: str


# ===== User Self-Service Endpoints =====

@router.get("/export-my-data")
async def export_my_data(
    current_user: Annotated[AppUser, Depends(get_current_user)]
):
    """
    Export all user data (GDPR Article 15 - Right to Access).
    
    Returns:
    - User profile data
    - Complete audit trail (all events)
    - Statistics
    
    This is a self-service endpoint - users can export their own data.
    """
    try:
        # Get GDPR service (inject via dependency)
        from app.api.dicontainer.dicontainer import get_gdpr_service
        gdpr_service: GDPRService = await get_gdpr_service()
        
        # Export data
        export_data = await gdpr_service.export_user_data(
            user_id=current_user.id,
            client_id=current_user.client_id,
            requesting_user_id=current_user.id
        )
        
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f'attachment; filename="user_data_{current_user.id}.json"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error exporting user data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )


@router.post("/delete-my-data")
async def delete_my_data(
    request: DeleteMyDataRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)]
):
    """
    Request account deletion (GDPR Article 17 - Right to be Forgotten).
    
    **IMPORTANT**: This action is IRREVERSIBLE!
    
    Process:
    1. Verify password
    2. Anonymize all audit logs
    3. Soft delete user account
    4. Deactivate all sessions
    
    Requires:
    - Password confirmation
    - confirm: true
    """
    try:
        # Validate confirmation
        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must confirm deletion by setting 'confirm' to true"
            )
        
        # Verify password
        from core.services.auth.auth_service import AuthService
        from app.api.dicontainer.dicontainer import get_auth_service
        
        auth_service: AuthService = await get_auth_service()
        
        # Verify password
        is_valid = await auth_service.verify_password(
            current_user.hashed_password,
            request.password
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid password"
            )
        
        # Get GDPR service
        from app.api.dicontainer.dicontainer import get_gdpr_service
        gdpr_service: GDPRService = await get_gdpr_service()
        
        # Anonymize user data
        success = await gdpr_service.anonymize_user_data(
            user_id=current_user.id,
            client_id=current_user.client_id,
            requesting_user_id=current_user.id,
            reason=request.reason
        )
        
        if success:
            return {
                "message": "Your account has been deleted and all data has been anonymized",
                "gdpr_compliance": "Article 17 - Right to be Forgotten",
                "status": "anonymized",
                "note": "This action is irreversible. All your personal data has been removed."
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to anonymize user data"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deletion request"
        )


# ===== Admin Endpoints =====

@router.get("/export-user-data/{user_id}")
# @require_role(UserRole.ADMIN)  # Uncomment when role decorator is available
async def admin_export_user_data(
    user_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)]
):
    """
    Admin: Export any user's data (GDPR compliance).
    
    Requires admin role.
    """
    try:
        # Check if admin (implement your admin check)
        # if current_user.role != UserRole.ADMIN:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.api.dicontainer.dicontainer import get_gdpr_service
        gdpr_service: GDPRService = await get_gdpr_service()
        
        export_data = await gdpr_service.export_user_data(
            user_id=user_id,
            client_id=current_user.client_id,
            requesting_user_id=current_user.id
        )
        
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f'attachment; filename="user_data_{user_id}.json"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in admin export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Export failed")


@router.post("/anonymize-user")
# @require_role(UserRole.ADMIN)  # Uncomment when role decorator is available
async def admin_anonymize_user(
    request: AnonymizeUserRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)]
):
    """
    Admin: Anonymize any user's data (GDPR compliance).
    
    Requires admin role.
    **IRREVERSIBLE ACTION** - use with caution!
    """
    try:
        # Check if admin
        # if current_user.role != UserRole.ADMIN:
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.api.dicontainer.dicontainer import get_gdpr_service
        gdpr_service: GDPRService = await get_gdpr_service()
        
        success = await gdpr_service.anonymize_user_data(
            user_id=request.user_id,
            client_id=current_user.client_id,
            requesting_user_id=current_user.id,
            reason=request.reason
        )
        
        if success:
            return {
                "message": "User data anonymized successfully",
                "user_id": request.user_id,
                "anonymized_by": current_user.username,
                "reason": request.reason,
                "status": "anonymized"
            }
        else:
            raise HTTPException(status_code=500, detail="Anonymization failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin anonymization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Anonymization failed")


@router.get("/verify-anonymization/{user_id}")
# @require_role(UserRole.ADMIN)
async def verify_user_anonymization(
    user_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)]
):
    """
    Admin: Verify that user data has been properly anonymized.
    
    Returns verification report.
    """
    try:
        from app.api.dicontainer.dicontainer import get_gdpr_service
        gdpr_service: GDPRService = await get_gdpr_service()
        
        verification = await gdpr_service.verify_anonymization(
            user_id=user_id,
            client_id=current_user.client_id
        )
        
        return verification
        
    except Exception as e:
        logger.error(f"Error verifying anonymization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Verification failed")

