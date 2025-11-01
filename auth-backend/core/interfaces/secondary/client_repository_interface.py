"""
Client Repository Interface
Defines contract for client persistence (Secondary Port)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.client.client import Client


class IClientRepository(ABC):
    """
    Repository interface for client persistence.
    
    Following Dependency Inversion Principle - domain depends on abstraction.
    """
    
    @abstractmethod
    async def save(self, client: Client) -> Client:
        """
        Save or update client.
        
        Contract:
        - If client.id is None: Creates new client
        - If client.id is set: Updates existing client
        
        Raises:
            ValueError: If client.id is set but client doesn't exist (attempting to update non-existent client)
            
        Note: This exception is acceptable because it indicates a business logic error
        (trying to update a client that was deleted or never existed). The service layer
        should verify existence before calling save() for updates.
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, client_id: str) -> Optional[Client]:
        """Find client by ID"""
        pass
    
    @abstractmethod
    async def find_by_subdomain(self, subdomain: str) -> Optional[Client]:
        """Find client by subdomain"""
        pass
    
    @abstractmethod
    async def find_by_api_key(self, api_key: str) -> Optional[Client]:
        """Find client by API key"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Client]:
        """Find all clients"""
        pass
    
    @abstractmethod
    async def delete(self, client_id: str) -> bool:
        """Delete client by ID"""
        pass

