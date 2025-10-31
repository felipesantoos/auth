"""
Client API Mapper
Maps between domain models and API DTOs
"""
from core.domain.client.client import Client
from app.api.dtos.response.client_response import ClientResponse, ClientResponseWithApiKey


class ClientMapper:
    """Mapper for Client domain model <-> API DTOs"""
    
    @staticmethod
    def to_response(client: Client, include_api_key: bool = False) -> ClientResponse | ClientResponseWithApiKey:
        """Convert domain model to response DTO"""
        if include_api_key and client.api_key:
            return ClientResponseWithApiKey(
                id=client.id,
                name=client.name,
                subdomain=client.subdomain,
                active=client.active,
                api_key=client.api_key,
                created_at=client.created_at,
                updated_at=client.updated_at,
            )
        else:
            return ClientResponse(
                id=client.id,
                name=client.name,
                subdomain=client.subdomain,
                active=client.active,
                created_at=client.created_at,
                updated_at=client.updated_at,
            )

