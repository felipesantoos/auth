"""
Client Service Implementation
Orchestrates client business logic
"""
import logging
from typing import List, Optional
from datetime import datetime
from core.interfaces.primary.client_service_interface import ClientServiceInterface
from core.interfaces.secondary.client_repository_interface import ClientRepositoryInterface
from core.domain.client.client import Client

logger = logging.getLogger(__name__)


class ClientService(ClientServiceInterface):
    """
    Service implementation - orchestrates client business logic.
    
    Following:
    - Single Responsibility (only client management logic)
    - Dependency Inversion (depends on interfaces)
    - Open/Closed (extend via new methods)
    """
    
    def __init__(self, repository: ClientRepositoryInterface):
        """
        Constructor injection for testability.
        
        Args:
            repository: Repository interface (injected)
        """
        self.repository = repository
    
    async def create_client(self, name: str, subdomain: str) -> Client:
        """
        Create a new client (tenant).
        
        We check for existing subdomain to ensure uniqueness, as subdomains are used
        for tenant identification in multi-tenant routing.
        """
        existing = await self.repository.find_by_subdomain(subdomain)
        if existing:
            raise ValueError(f"Client with subdomain '{subdomain}' already exists")
        
        # Normalize subdomain to lowercase for consistent URL matching
        client = Client(
            id=None,
            name=name,
            subdomain=subdomain.lower(),
            api_key=None,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        client.validate()
        
        # Generate API key immediately on creation for client API access
        client.generate_api_key()
        
        return await self.repository.save(client)
    
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        return await self.repository.find_by_id(client_id)
    
    async def get_client_by_subdomain(self, subdomain: str) -> Optional[Client]:
        """Get client by subdomain"""
        return await self.repository.find_by_subdomain(subdomain.lower())
    
    async def list_all_clients(self) -> List[Client]:
        """List all clients (admin only)"""
        return await self.repository.find_all()
    
    async def update_client(self, client: Client) -> Client:
        """Update client"""
        client.validate()
        # Update timestamp to track when client was last modified
        client.updated_at = datetime.utcnow()
        return await self.repository.save(client)
    
    async def delete_client(self, client_id: str) -> bool:
        """
        Delete client by ID.
        
        We verify existence first to provide a clearer error message before attempting deletion.
        """
        client = await self.repository.find_by_id(client_id)
        if not client:
            raise ValueError("Client not found")
        
        return await self.repository.delete(client_id)
    
    async def regenerate_api_key(self, client_id: str) -> str:
        """
        Regenerate API key for client.
        
        Used when a key is compromised or rotated for security. The old key becomes
        invalid immediately after this operation.
        """
        client = await self.repository.find_by_id(client_id)
        if not client:
            raise ValueError("Client not found")
        
        new_key = client.generate_api_key()
        client.updated_at = datetime.utcnow()
        await self.repository.save(client)
        
        return new_key

