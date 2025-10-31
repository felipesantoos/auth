"""
Authorization Decorators and Utilities
Role-based access control (RBAC)
Adapted for multi-tenant architecture
"""
import logging
from functools import wraps
from typing import List, Callable, Optional
from fastapi import HTTPException, status
from core.domain.auth.user_role import UserRole
from core.domain.auth.app_user import AppUser
from core.exceptions import ForbiddenException

logger = logging.getLogger(__name__)


def require_role(*allowed_roles: UserRole):
    """
    Decorator to require specific roles for endpoint access
    
    Usage:
        @router.delete("/{id}")
        @require_role(UserRole.ADMIN)
        async def delete_entity(current_user: AppUser = Depends(get_current_user)):
            ...
    
    Args:
        *allowed_roles: Roles that are allowed to access the endpoint
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                logger.error("current_user not found in function parameters")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization error: user context not found"
                )
            
            # Check if user has required role
            if current_user.role not in allowed_roles:
                logger.warning(
                    f"Access denied - insufficient permissions",
                    extra={
                        "user_id": current_user.id,
                        "user_role": current_user.role,
                        "required_roles": [r.value for r in allowed_roles],
                        "endpoint": func.__name__
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
                )
            
            logger.debug(
                f"Access granted",
                extra={
                    "user_id": current_user.id,
                    "user_role": current_user.role,
                    "endpoint": func.__name__
                }
            )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable):
    """
    Shortcut decorator to require ADMIN role
    
    Usage:
        @router.post("/admin-action")
        @require_admin
        async def admin_action(current_user: AppUser = Depends(get_current_user)):
            ...
    """
    return require_role(UserRole.ADMIN)(func)


def require_manager_or_admin(func: Callable):
    """
    Shortcut decorator to require MANAGER or ADMIN role
    
    Usage:
        @router.put("/{id}")
        @require_manager_or_admin
        async def update_entity(current_user: AppUser = Depends(get_current_user)):
            ...
    """
    return require_role(UserRole.ADMIN, UserRole.MANAGER)(func)


def check_ownership(user: AppUser, resource_user_id: str, resource_client_id: Optional[str] = None) -> bool:
    """
    Check if user owns the resource or is admin/manager (multi-tenant).
    
    Also validates that resource belongs to same client as user.
    
    Args:
        user: Current authenticated user
        resource_user_id: ID of the user who owns the resource
        resource_client_id: Optional client_id of the resource
        
    Returns:
        True if user can access, False otherwise
    """
    # Multi-tenant: Resource must belong to same client
    if resource_client_id and user.client_id != resource_client_id:
        return False
    
    # Admins and managers can access any resource within their client
    if user.role in [UserRole.ADMIN, UserRole.MANAGER]:
        return True
    
    # Regular users can only access their own resources
    return user.id == resource_user_id


def ensure_ownership(user: AppUser, resource_user_id: str, resource_client_id: Optional[str] = None):
    """
    Ensure user owns the resource or has admin/manager role (multi-tenant).
    
    Raises ForbiddenException if user doesn't have access.
    
    Usage:
        @router.get("/users/{user_id}/profile")
        async def get_profile(user_id: str, current_user: AppUser = Depends(get_current_user)):
            ensure_ownership(current_user, user_id)
            # ... rest of logic
    """
    if not check_ownership(user, resource_user_id, resource_client_id):
        logger.warning(
            "Ownership check failed",
            extra={
                "user_id": user.id,
                "resource_user_id": resource_user_id,
                "resource_client_id": resource_client_id,
                "user_client_id": user.client_id,
                "user_role": user.role
            }
        )
        raise ForbiddenException("You don't have permission to access this resource")

