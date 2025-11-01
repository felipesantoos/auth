"""
API Key Request DTOs
"""
from pydantic import BaseModel, Field
from typing import List
from core.domain.auth.api_key_scope import ApiKeyScope


class CreateApiKeyRequest(BaseModel):
    """Request to create API key"""
    name: str = Field(..., min_length=3, max_length=100, description="Friendly name for the API key")
    scopes: List[str] = Field(..., min_items=1, description="List of permission scopes")
    expires_in_days: int = Field(default=365, ge=1, le=3650, description="Expiration in days (1-3650)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Integration",
                "scopes": ["read:user", "write:user"],
                "expires_in_days": 365
            }
        }


class RevokeApiKeyRequest(BaseModel):
    """Request to revoke API key (ID in path)"""
    pass

