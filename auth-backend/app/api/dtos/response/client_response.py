"""
Client Response DTOs
Pydantic models for API responses
"""
from pydantic import BaseModel
from datetime import datetime


class ClientResponse(BaseModel):
    """Response DTO for client data"""
    id: str
    name: str
    subdomain: str
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClientResponseWithApiKey(ClientResponse):
    """Response DTO for client data including API key (only on creation/regeneration)"""
    api_key: str

