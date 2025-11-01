"""
Client Repository Implementation
PostgreSQL implementation of ClientRepositoryInterface
"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DatabaseError
from core.interfaces.secondary.client_repository_interface import IClientRepository
from core.domain.client.client import Client
from infra.database.models.client import DBClient
from infra.database.mappers.client_mapper import ClientMapper
from core.exceptions import (
    DomainException,
    DuplicateEntityException,
    EntityNotFoundException,
    IntegrityException,
)

logger = logging.getLogger(__name__)


class ClientRepository(IClientRepository):
    """
    PostgreSQL implementation of IClientRepository.
    
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
        """
        Save client with error handling.
        
        Translates database errors to domain exceptions.
        
        Raises:
            EntityNotFoundException: If trying to update non-existent client
            DuplicateEntityException: If unique constraint violation (subdomain)
            DomainException: If other database error occurs
        """
        try:
            if client.id:
                # Update existing
                result = await self.session.execute(
                    select(DBClient).where(DBClient.id == client.id)
                )
                db_client = result.scalar_one_or_none()
                
                if not db_client:
                    raise EntityNotFoundException("Client", client.id)
                
                ClientMapper.to_database(client, db_client)
            else:
                # Create new
                db_client = ClientMapper.to_database(client)
                self.session.add(db_client)
            
            await self.session.flush()
            await self.session.refresh(db_client)
            
            return ClientMapper.to_domain(db_client)
            
        except EntityNotFoundException:
            # Expected domain exception - let it propagate
            raise
        except IntegrityError as e:
            # Database constraint violation (unique, foreign key, etc.)
            logger.warning(f"Integrity error saving client: {e}")
            
            # Parse error to provide meaningful message
            error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
            
            if 'unique' in error_str:
                if 'subdomain' in error_str:
                    # Unique constraint on subdomain
                    raise DuplicateEntityException("Client", "subdomain", client.subdomain)
                else:
                    # Other unique constraint
                    raise DuplicateEntityException("Client", "unknown", "value")
            elif 'foreign key' in error_str:
                # Foreign key violation
                raise DomainException(
                    "Cannot save client due to referential integrity",
                    "REFERENTIAL_INTEGRITY_ERROR"
                )
            else:
                # Other integrity error
                raise DomainException(
                    "Cannot save client due to data integrity rules",
                    "DATA_INTEGRITY_ERROR"
                )
        except DatabaseError as e:
            # Database connection or query error
            logger.error(f"Database error saving client: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except SQLAlchemyError as e:
            # Other SQLAlchemy errors
            logger.error(f"SQLAlchemy error saving client: {e}", exc_info=True)
            raise DomainException("Failed to save client", "REPOSITORY_ERROR")
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error saving client: {e}", exc_info=True)
            raise DomainException("Unexpected error saving client", "UNEXPECTED_REPOSITORY_ERROR")
    
    async def find_by_id(self, client_id: str) -> Optional[Client]:
        """
        Find client by ID.
        
        Returns None if not found (NOT an exception).
        """
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.id == client_id)
            )
            db_client = result.scalar_one_or_none()
            
            if db_client:
                return ClientMapper.to_domain(db_client)
            return None
            
        except DatabaseError as e:
            logger.error(f"Database error finding client {client_id}: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error finding client {client_id}: {e}", exc_info=True)
            raise DomainException("Failed to find client", "REPOSITORY_ERROR")
    
    async def find_by_subdomain(self, subdomain: str) -> Optional[Client]:
        """
        Find client by subdomain.
        
        Returns None if not found (NOT an exception).
        """
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.subdomain == subdomain.lower())
            )
            db_client = result.scalar_one_or_none()
            
            if db_client:
                return ClientMapper.to_domain(db_client)
            return None
            
        except DatabaseError as e:
            logger.error(f"Database error finding client by subdomain {subdomain}: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error finding client by subdomain {subdomain}: {e}", exc_info=True)
            raise DomainException("Failed to find client", "REPOSITORY_ERROR")
    
    async def find_by_api_key(self, api_key: str) -> Optional[Client]:
        """
        Find client by API key.
        
        Returns None if not found (NOT an exception).
        """
        try:
            result = await self.session.execute(
                select(DBClient).where(DBClient.api_key == api_key)
            )
            db_client = result.scalar_one_or_none()
            
            if db_client:
                return ClientMapper.to_domain(db_client)
            return None
            
        except DatabaseError as e:
            logger.error(f"Database error finding client by API key: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error finding client by API key: {e}", exc_info=True)
            raise DomainException("Failed to find client", "REPOSITORY_ERROR")
    
    async def find_all(self) -> List[Client]:
        """
        Find all clients.
        
        Returns empty list if error (graceful degradation).
        """
        try:
            result = await self.session.execute(select(DBClient))
            db_clients = result.scalars().all()
            
            return [ClientMapper.to_domain(db_client) for db_client in db_clients]
            
        except DatabaseError as e:
            logger.error(f"Database error listing clients: {e}", exc_info=True)
            # Graceful degradation: return empty list
            return []
        except Exception as e:
            logger.error(f"Error listing clients: {e}", exc_info=True)
            # Graceful degradation: return empty list
            return []
    
    async def delete(self, client_id: str) -> bool:
        """
        Delete client with error handling.
        
        Raises:
            IntegrityException: If client has related records (foreign key constraint)
            DomainException: If other database error occurs
        """
        try:
            query = sql_delete(DBClient).where(DBClient.id == client_id)
            result = await self.session.execute(query)
            await self.session.flush()
            
            return result.rowcount > 0
            
        except IntegrityError as e:
            # Foreign key constraint (client has related records)
            logger.warning(f"Cannot delete client {client_id} - has related records: {e}")
            raise IntegrityException(
                "Client",
                client_id,
                dependent_entities=["users", "other related records"]
            )
        except DatabaseError as e:
            logger.error(f"Database error deleting client {client_id}: {e}", exc_info=True)
            raise DomainException("Database operation failed", "DATABASE_ERROR")
        except Exception as e:
            logger.error(f"Error deleting client {client_id}: {e}", exc_info=True)
            raise DomainException("Failed to delete client", "REPOSITORY_ERROR")

