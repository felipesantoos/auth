"""
Tenant Middleware
Extracts client_id (tenant) from request for multi-tenant isolation
"""
from fastapi import Request, HTTPException, status
from typing import Optional
from core.interfaces.secondary.client_repository_interface import IClientRepository


def get_client_id_from_request(request: Request) -> Optional[str]:
    """
    Extract client_id from request.
    
    Checks in order:
    1. X-Client-ID header (for API calls)
    2. X-Client-Subdomain header (converts to client_id)
    3. Subdomain from Host header (e.g., client1.example.com -> client1)
    4. Query parameter ?client_id (development only)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client ID if found, None otherwise
    """
    # 1. Check X-Client-ID header (direct client ID)
    client_id = request.headers.get("X-Client-ID")
    if client_id:
        return client_id
    
    # 2. Check X-Client-Subdomain header (convert to client_id)
    subdomain = request.headers.get("X-Client-Subdomain")
    if subdomain:
        # Will need to lookup client_id from subdomain
        # For now, return None - will be handled by get_client_from_request
        pass
    
    # 3. Extract from Host subdomain (e.g., client1.example.com -> client1)
    host = request.headers.get("host", "")
    if host:
        # Extract subdomain (first part before first dot)
        parts = host.split(".")
        if len(parts) > 2:  # Has subdomain
            subdomain = parts[0]
            # Will need to lookup - handled by get_client_from_request
    
    # 4. Query parameter (development only)
    client_id = request.query_params.get("client_id")
    if client_id:
        return client_id
    
    return None


async def get_client_from_request(
    request: Request,
    client_repository: Optional[IClientRepository] = None
) -> Optional[str]:
    """
    Get client_id from request, looking up by subdomain if needed.
    
    Args:
        request: FastAPI request object
        client_repository: Optional repository to lookup by subdomain
        
    Returns:
        Client ID if found, None otherwise
    """
    # Try direct client_id first
    client_id = get_client_id_from_request(request)
    if client_id:
        return client_id
    
    # Try to extract from subdomain
    subdomain = request.headers.get("X-Client-Subdomain")
    if not subdomain:
        host = request.headers.get("host", "")
        if host:
            parts = host.split(".")
            if len(parts) > 2:
                subdomain = parts[0]
    
    if subdomain and client_repository:
        try:
            client = await client_repository.find_by_subdomain(subdomain)
            if client:
                return client.id
        except Exception:
            pass
    
    return None

