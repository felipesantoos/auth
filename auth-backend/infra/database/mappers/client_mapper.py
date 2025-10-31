"""
Client Mapper
Maps between domain models and database models
"""
from core.domain.client.client import Client
from infra.database.models.client import DBClient


class ClientMapper:
    """Mapper for Client domain model <-> DBClient database model"""
    
    @staticmethod
    def to_domain(db_client: DBClient) -> Client:
        """Convert database model to domain model"""
        return Client(
            id=db_client.id,
            name=db_client.name,
            subdomain=db_client.subdomain,
            active=db_client.active,
            created_at=db_client.created_at,
            updated_at=db_client.updated_at,
            _api_key=db_client.api_key,  # Use protected field for encapsulation
        )
    
    @staticmethod
    def to_database(client: Client, db_client: DBClient = None) -> DBClient:
        """Convert domain model to database model"""
        if db_client is None:
            db_client = DBClient()
        
        db_client.id = client.id
        db_client.name = client.name
        db_client.subdomain = client.subdomain
        db_client.api_key = client.api_key  # Access via property (encapsulation)
        db_client.active = client.active
        db_client.created_at = client.created_at
        db_client.updated_at = client.updated_at
        
        return db_client

