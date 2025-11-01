"""
Permission Routes
Fine-grained permission management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated
import logging

from app.api.middlewares.auth_middleware import get_current_user, require_role
from app.api.dicontainer.dicontainer import get_permission_service
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.domain.auth.permission import PermissionAction  # ResourceType removed! ✨
from core.services.auth.permission_service import PermissionService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/permissions", tags=["Permissions"])


# DTOs
class GrantPermissionRequest(BaseModel):
    """
    Request to grant permission.
    
    resource_type can be ANY string (e.g., "ticket", "project", "order")
    """
    user_id: str
    resource_type: str  # String livre! "ticket", "project", "invoice", etc.
    action: str
    resource_id: str = None


class PermissionResponse(BaseModel):
    """Permission response"""
    id: str
    user_id: str
    client_id: str
    resource_type: str
    resource_id: str = None
    action: str
    granted_by: str = None
    created_at: str


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def grant_permission(
    request: GrantPermissionRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    permission_service: Annotated[PermissionService, Depends(get_permission_service)],
    _: None = Depends(require_role(UserRole.ADMIN))  # Admin only
):
    """
    Grant permission to user (admin only).
    
    Allows assigning fine-grained permissions to users for specific resources.
    """
    try:
        # Normalize resource_type (free string!)
        resource_type = request.resource_type.lower().strip()
        
        # Parse action enum
        action = PermissionAction(request.action)
        
        # Grant permission
        permission = await permission_service.grant_permission(
            granter=current_user,
            user_id=request.user_id,
            resource_type=resource_type,  # String! ✨
            action=action,
            resource_id=request.resource_id
        )
        
        return PermissionResponse(
            id=permission.id,
            user_id=permission.user_id,
            client_id=permission.client_id,
            resource_type=permission.resource_type,  # String direto! ✨
            resource_id=permission.resource_id,
            action=permission.action.value,
            granted_by=permission.granted_by,
            created_at=permission.created_at.isoformat() if permission.created_at else None
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error granting permission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant permission"
        )


@router.get("/user/{user_id}", response_model=List[PermissionResponse])
async def list_user_permissions(
    user_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    permission_service: Annotated[PermissionService, Depends(get_permission_service)]
):
    """
    List user's permissions.
    
    Users can only see their own permissions unless they are admin.
    """
    # Check authorization
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own permissions"
        )
    
    try:
        permissions = await permission_service.list_user_permissions(
            user_id=user_id,
            client_id=current_user.client_id
        )
        
        return [
            PermissionResponse(
                id=p.id,
                user_id=p.user_id,
                client_id=p.client_id,
                resource_type=p.resource_type,  # String direto! ✨
                resource_id=p.resource_id,
                action=p.action.value,
                granted_by=p.granted_by,
                created_at=p.created_at.isoformat() if p.created_at else None
            )
            for p in permissions
        ]
        
    except Exception as e:
        logger.error(f"Error listing permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list permissions"
        )


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    permission_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    permission_service: Annotated[PermissionService, Depends(get_permission_service)]
):
    """
    Revoke permission.
    
    Only admin or the user who granted the permission can revoke it.
    """
    try:
        result = await permission_service.revoke_permission(
            revoker=current_user,
            permission_id=permission_id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error revoking permission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke permission"
        )

