"""
Client Request DTOs
Pydantic models for request validation
"""
from pydantic import BaseModel, Field


class CreateClientRequest(BaseModel):
    """Request DTO for creating a client"""
    name: str = Field(..., min_length=3, max_length=200, description="Client name")
    subdomain: str = Field(..., min_length=2, max_length=100, description="Client subdomain")


class UpdateClientRequest(BaseModel):
    """Request DTO for updating a client"""
    name: str | None = Field(None, min_length=3, max_length=200, description="Client name")
    active: bool | None = Field(None, description="Client active status")

