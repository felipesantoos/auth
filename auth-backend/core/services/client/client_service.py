"""
Client Service Implementation
Orchestrates client business logic
"""
import logging
from typing import List, Optional
from datetime import datetime
from core.interfaces.primary.client_service_interface import IClientService
from core.interfaces.secondary.client_repository_interface import IClientRepository
from core.domain.client.client import Client
from core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    ValidationException,
    DomainException,
)

logger = logging.getLogger(__name__)


class ClientService(IClientService):
    """
    Service implementation - orchestrates client business logic.
    
    Following:
    - Single Responsibility (only client management logic)
    - Dependency Inversion (depends on interfaces)
    - Open/Closed (extend via new methods)
    """
    
    def __init__(self, repository: IClientRepository):
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
        
        Raises:
            DuplicateEntityException: If subdomain already exists
            ValidationException: If validation fails
            DomainException: If technical error occurs
        """
        try:
            existing = await self.repository.find_by_subdomain(subdomain)
            if existing:
                raise DuplicateEntityException("Client", "subdomain", subdomain)
            
            # Normalize subdomain to lowercase for consistent URL matching
            client = Client(
                id=None,
                name=name,
                subdomain=subdomain.lower(),
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                _api_key=None,  # Use protected field for encapsulation
            )
            
            client.validate()
            
            # Generate API key immediately on creation for client API access
            client.generate_api_key()
            
            created_client = await self.repository.save(client)
            logger.info("Client created successfully", extra={"client_id": created_client.id, "subdomain": subdomain})
            return created_client
            
        except (DuplicateEntityException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating client: {e}", exc_info=True, extra={"subdomain": subdomain})
            raise DomainException("Failed to create client due to technical error", "CLIENT_CREATION_FAILED")
    
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
        """
        Update client.
        
        Raises:
            ValidationException: If validation fails
            DomainException: If technical error occurs
        """
        try:
            client.validate()
            client.updated_at = datetime.utcnow()
            updated = await self.repository.save(client)
            logger.info("Client updated successfully", extra={"client_id": client.id})
            return updated
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating client: {e}", exc_info=True, extra={"client_id": client.id})
            raise DomainException("Failed to update client due to technical error", "CLIENT_UPDATE_FAILED")
    
    async def delete_client(self, client_id: str) -> bool:
        """
        Delete client by ID.
        
        We verify existence first to provide a clearer error message before attempting deletion.
        
        Raises:
            EntityNotFoundException: If client not found
            DomainException: If technical error occurs
        """
        try:
            client = await self.repository.find_by_id(client_id)
            if not client:
                raise EntityNotFoundException("Client", client_id)
            
            result = await self.repository.delete(client_id)
            if result:
                logger.info("Client deleted successfully", extra={"client_id": client_id})
            return result
            
        except EntityNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting client: {e}", exc_info=True, extra={"client_id": client_id})
            raise DomainException("Failed to delete client due to technical error", "CLIENT_DELETION_FAILED")
    
    async def regenerate_api_key(self, client_id: str) -> str:
        """
        Regenerate API key for client.
        
        Used when a key is compromised or rotated for security. The old key becomes
        invalid immediately after this operation.
        
        Raises:
            EntityNotFoundException: If client not found
            DomainException: If technical error occurs
        """
        try:
            client = await self.repository.find_by_id(client_id)
            if not client:
                raise EntityNotFoundException("Client", client_id)
            
            new_key = client.generate_api_key()
            client.updated_at = datetime.utcnow()
            await self.repository.save(client)
            
            logger.info("API key regenerated successfully", extra={"client_id": client_id})
            return new_key
            
        except EntityNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error regenerating API key: {e}", exc_info=True, extra={"client_id": client_id})
            raise DomainException("Failed to regenerate API key due to technical error", "API_KEY_REGENERATION_FAILED")

