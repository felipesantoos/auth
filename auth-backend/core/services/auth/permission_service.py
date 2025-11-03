"""
Permission Service
Fine-grained permission checking and management
"""
import logging
from typing import List, Optional
from core.domain.auth.permission import Permission, PermissionAction
from core.domain.auth.app_user import AppUser
# REMOVED: from core.domain.auth.user_role import UserRole (roles now in WorkspaceMember)
from core.interfaces.secondary.permission_repository_interface import IPermissionRepository

logger = logging.getLogger(__name__)


class PermissionService:
    """
    Service for fine-grained permission management.
    
    **Design Note**: resource_type is a free string (not enum) to allow
    maximum flexibility. Each system can define its own resource types.
    """
    
    def __init__(self, repository: IPermissionRepository):
        self.repository = repository
    
    async def has_permission(
        self,
        user: AppUser,
        resource_type: str,  # String livre! ✨
        action: PermissionAction,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission to perform action on resource.
        
        Args:
            user: User to check
            resource_type: Type of resource
            action: Action to perform
            resource_id: Specific resource ID (optional)
            
        Returns:
            True if user has permission
        """
        # REMOVED: Global admin bypass (admins are now per-workspace)
        # TODO: Implement workspace-aware admin bypass if needed
        
        # Get user's permissions for this resource type
        # Note: client_id needs to be passed explicitly (no longer in AppUser)
        client_id = getattr(user, 'client_id', 'default-client')
        permissions = await self.repository.find_by_user_and_resource_type(
            user.id, client_id, resource_type
        )
        
        # Check if any permission allows this action
        for permission in permissions:
            if permission.allows(action, resource_id):
                logger.info(f"Permission granted for user {user.id}: {action} on {resource_type}/{resource_id}")
                return True
        
        logger.warning(f"Permission denied for user {user.id}: {action} on {resource_type}/{resource_id}")
        return False
    
    async def grant_permission(
        self,
        granter: AppUser,
        user_id: str,
        resource_type: str,  # String livre! ✨
        action: PermissionAction,
        resource_id: Optional[str] = None
    ) -> Permission:
        """
        Grant permission to user.
        
        Args:
            granter: User granting permission (must be admin or have MANAGE permission)
            user_id: User receiving permission
            resource_type: Type of resource
            action: Action to allow
            resource_id: Specific resource ID (None = all resources)
            
        Returns:
            Created permission
            
        Raises:
            ValueError: If granter doesn't have permission to grant
        """
        # REMOVED: Global admin check (admins are now per-workspace)
        # Check if granter has MANAGE permission
        has_manage = await self.has_permission(
            granter, resource_type, PermissionAction.MANAGE, resource_id
        )
        if not has_manage:
            raise ValueError("You don't have permission to grant permissions")
        
        # Create permission
        # Note: client_id needs to be passed explicitly (no longer in AppUser)
        client_id = getattr(granter, 'client_id', 'default-client')
        
        permission = Permission(
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            granted_by=granter.id
        )
        
        saved = await self.repository.save(permission)
        logger.info(f"Permission granted by {granter.id} to {user_id}: {action} on {resource_type}/{resource_id}")
        
        return saved
    
    async def revoke_permission(
        self,
        revoker: AppUser,
        permission_id: str
    ) -> bool:
        """Revoke permission (admin or granter only)"""
        permission = await self.repository.find_by_id(permission_id)
        
        if not permission:
            return False
        
        # REMOVED: Global admin check (admins are now per-workspace)
        # Only the granter or a workspace admin can revoke
        if permission.granted_by != revoker.id:
            # TODO: Check if revoker is workspace admin
            raise ValueError("You don't have permission to revoke this permission")
        
        result = await self.repository.delete(permission_id)
        logger.info(f"Permission {permission_id} revoked by {revoker.id}")
        
        return result
    
    async def list_user_permissions(
        self,
        user_id: str,
        client_id: str
    ) -> List[Permission]:
        """List all permissions for user"""
        return await self.repository.find_by_user(user_id, client_id)

