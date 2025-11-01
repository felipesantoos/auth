"""
API Key Repository Interface
Port for API key persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.api_key import ApiKey


class ApiKeyRepositoryInterface(ABC):
    """Interface for API key repository operations"""
    
    @abstractmethod
    async def save(self, api_key: ApiKey) -> ApiKey:
        """Save API key"""
        pass
    
    @abstractmethod
    async def find_by_id(self, key_id: str) -> Optional[ApiKey]:
        """Find API key by ID"""
        pass
    
    @abstractmethod
    async def find_by_key_hash(self, key_hash: str) -> Optional[ApiKey]:
        """Find API key by hash"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, client_id: str) -> List[ApiKey]:
        """Find all API keys for a user"""
        pass
    
    @abstractmethod
    async def find_active_by_user(self, user_id: str, client_id: str) -> List[ApiKey]:
        """Find active API keys for a user"""
        pass
    
    @abstractmethod
    async def count_by_user(self, user_id: str, client_id: str) -> int:
        """Count API keys for a user"""
        pass

