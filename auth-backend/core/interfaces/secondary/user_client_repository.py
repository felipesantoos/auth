"""User Client Repository Interface"""
from abc import ABC, abstractmethod
from typing import List, Optional
from infra.database.models.user_client import DBUserClient


class IUserClientRepository(ABC):
    """Interface for user-client access data persistence"""
    
    @abstractmethod
    async def save(self, user_client: DBUserClient) -> DBUserClient:
        """Save or update user-client access"""
        pass
    
    @abstractmethod
    async def find_by_user_and_client(
        self, user_id: str, client_id: str
    ) -> Optional[DBUserClient]:
        """Find user-client access by user and client"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, active_only: bool = True) -> List[DBUserClient]:
        """Find all client accesses for a user"""
        pass
    
    @abstractmethod
    async def find_by_client(self, client_id: str, active_only: bool = True) -> List[DBUserClient]:
        """Find all user accesses for a client"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str, client_id: str) -> bool:
        """Delete user-client access"""
        pass

