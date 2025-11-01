"""
Client Service Interface
Defines contract for client business operations (Primary Port)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.client.client import Client


class IClientService(ABC):
    """
    Service interface for client business operations.
    
    Following Dependency Inversion Principle - API depends on abstraction.
    """
    
    @abstractmethod
    async def create_client(self, name: str, subdomain: str) -> Client:
        """Create a new client"""
        pass
    
    @abstractmethod
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        pass
    
    @abstractmethod
    async def get_client_by_subdomain(self, subdomain: str) -> Optional[Client]:
        """Get client by subdomain"""
        pass
    
    @abstractmethod
    async def list_all_clients(self) -> List[Client]:
        """List all clients (admin only)"""
        pass
    
    @abstractmethod
    async def update_client(self, client: Client) -> Client:
        """Update client"""
        pass
    
    @abstractmethod
    async def delete_client(self, client_id: str) -> bool:
        """Delete client"""
        pass
    
    @abstractmethod
    async def regenerate_api_key(self, client_id: str) -> str:
        """Regenerate API key for client"""
        pass

