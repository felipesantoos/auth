"""
Permission Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.permission import Permission


class IPermissionRepository(ABC):
    """Repository interface for permissions"""
    
    @abstractmethod
    async def save(self, permission: Permission) -> Permission:
        """Save permission"""
        pass
    
    @abstractmethod
    async def find_by_id(self, permission_id: str) -> Optional[Permission]:
        """Find permission by ID"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, client_id: str) -> List[Permission]:
        """Find all permissions for user"""
        pass
    
    @abstractmethod
    async def find_by_user_and_resource_type(
        self, user_id: str, client_id: str, resource_type: str  # String livre! ✨
    ) -> List[Permission]:
        """Find permissions for user and specific resource type"""
        pass
    
    @abstractmethod
    async def delete(self, permission_id: str) -> bool:
        """Delete permission"""
        pass

