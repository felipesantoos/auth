"""
Client Routes
API endpoints for client management (admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from core.interfaces.primary.client_service_interface import IClientService
from app.api.dtos.request.client_request import CreateClientRequest, UpdateClientRequest
from app.api.dtos.response.client_response import ClientResponse, ClientResponseWithApiKey
from app.api.mappers.client_mapper import ClientMapper
from app.api.dicontainer.dicontainer import get_client_service

router = APIRouter(prefix="/api/v1/clients", tags=["Clients"])


@router.post("", response_model=ClientResponseWithApiKey, status_code=status.HTTP_201_CREATED)
async def create_client(
    request: CreateClientRequest,
    response: Response,
    service: IClientService = Depends(get_client_service),
):
    """
    Create a new client (tenant).
    
    Requires admin authentication (to be implemented).
    """
    try:
        client = await service.create_client(request.name, request.subdomain)
        
        # Add Location header pointing to created resource
        response.headers["Location"] = f"/api/v1/clients/{client.id}"
        
        return ClientMapper.to_response(client, include_api_key=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    service: IClientService = Depends(get_client_service),
):
    """
    List all clients (admin only).
    
    Requires admin authentication (to be implemented).
    """
    clients = await service.list_all_clients()
    return [ClientMapper.to_response(client) for client in clients]


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    service: IClientService = Depends(get_client_service),
):
    """
    Get client by ID (admin only).
    
    Requires admin authentication (to be implemented).
    """
    client = await service.get_client_by_id(client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return ClientMapper.to_response(client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: UpdateClientRequest,
    service: IClientService = Depends(get_client_service),
):
    """
    Update client (admin only).
    
    Requires admin authentication (to be implemented).
    """
    client = await service.get_client_by_id(client_id)
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Update fields if provided
    if request.name is not None:
        client.name = request.name
    if request.active is not None:
        client.active = request.active
    
    updated_client = await service.update_client(client)
    
    return ClientMapper.to_response(updated_client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    service: IClientService = Depends(get_client_service),
):
    """
    Delete client (admin only).
    
    Requires admin authentication (to be implemented).
    """
    try:
        success = await service.delete_client(client_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{client_id}/regenerate-api-key", response_model=ClientResponseWithApiKey)
async def regenerate_api_key(
    client_id: str,
    service: IClientService = Depends(get_client_service),
):
    """
    Regenerate API key for client (admin only).
    
    Requires admin authentication (to be implemented).
    """
    try:
        new_key = await service.regenerate_api_key(client_id)
        client = await service.get_client_by_id(client_id)
        return ClientMapper.to_response(client, include_api_key=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

