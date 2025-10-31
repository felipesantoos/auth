"""
Client Repository Implementation
PostgreSQL implementation of ClientRepositoryInterface
"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.interfaces.secondary.client_repository_interface import ClientRepositoryInterface
from core.domain.client.client import Client
from infra.database.models.client import DBClient
from infra.database.mappers.client_mapper import ClientMapper

logger = logging.getLogger(__name__)


class ClientRepository(ClientRepositoryInterface):
    """
    PostgreSQL implementation of ClientRepositoryInterface.
    
    This is a secondary adapter - implements the repository interface.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Constructor injection of database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def save(self, client: Client) -> Client:
        """Save or update client"""
        try:
            if client.id:
                # Update existing
                result = await self.session.execute(
                    select(DBClient).where(DBClient.id == client.id)
                )
                db_client = result.scalar_one_or_none()
                
                if not db_client:
                    raise ValueError(f"Client with id {client.id} not found")
                
                ClientMapper.to_database(client, db_client)
            else:
                # Create new
                db_client = ClientMapper.to_database(client)
                self.session.add(db_client)
            
            await self.session.flush()
            await self.session.refresh(db_client)
            
            return ClientMapper.to_domain(db_client)
            
        except Exception as e:
            logger.error(f"Error saving client: {str(e)}")
            raise
    
    async def find_by_id(self, client_id: str) -> Optional[Client]:
        """Find client by ID"""
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.id == client_id)
            )
            db_client = result.scalar_one_or_none()
            
            if db_client:
                return ClientMapper.to_domain(db_client)
            return None
            
        except Exception as e:
            logger.error(f"Error finding client by id: {str(e)}")
            raise
    
    async def find_by_subdomain(self, subdomain: str) -> Optional[Client]:
        """Find client by subdomain"""
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.subdomain == subdomain.lower())
            )
            db_client = result.scalar_one_or_none()
            
            if db_client:
                return ClientMapper.to_domain(db_client)
            return None
            
        except Exception as e:
            logger.error(f"Error finding client by subdomain: {str(e)}")
            raise
    
    async def find_by_api_key(self, api_key: str) -> Optional[Client]:
        """Find client by API key"""
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.api_key == api_key)
            )
            db_client = result.scalar_one_or_none()
            
            if db_client:
                return ClientMapper.to_domain(db_client)
            return None
            
        except Exception as e:
            logger.error(f"Error finding client by api_key: {str(e)}")
            raise
    
    async def find_all(self) -> List[Client]:
        """Find all clients"""
        try:
            result = await self.session.execute(select(DBClient))
            db_clients = result.scalars().all()
            
            return [ClientMapper.to_domain(db_client) for db_client in db_clients]
            
        except Exception as e:
            logger.error(f"Error finding all clients: {str(e)}")
            raise
    
    async def delete(self, client_id: str) -> bool:
        """Delete client by ID"""
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.id == client_id)
            )
            db_client = result.scalar_one_or_none()
            
            if not db_client:
                return False
            
            await self.session.delete(db_client)
            await self.session.flush()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting client: {str(e)}")
            raise

