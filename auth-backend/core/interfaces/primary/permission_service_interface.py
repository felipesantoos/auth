"""
Permission Service Interface
Port for permission operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.permission import Permission, PermissionAction
from core.domain.auth.app_user import AppUser


class IPermissionService(ABC):
    """Interface for permission service operations"""
    
    @abstractmethod
    async def has_permission(
        self,
        user: AppUser,
        resource_type: str,  # String livre! ✨
        action: PermissionAction,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user has permission"""
        pass
    
    @abstractmethod
    async def grant_permission(
        self,
        granter: AppUser,
        user_id: str,
        resource_type: str,  # String livre! ✨
        action: PermissionAction,
        resource_id: Optional[str] = None
    ) -> Permission:
        """Grant permission to user"""
        pass
    
    @abstractmethod
    async def revoke_permission(
        self,
        revoker: AppUser,
        permission_id: str
    ) -> bool:
        """Revoke permission"""
        pass
    
    @abstractmethod
    async def list_user_permissions(
        self,
        user_id: str,
        client_id: str
    ) -> List[Permission]:
        """List all permissions for user"""
        pass

