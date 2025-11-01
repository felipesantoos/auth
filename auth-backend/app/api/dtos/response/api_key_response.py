"""
API Key Response DTOs
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ApiKeyResponse(BaseModel):
    """Response for API key info (without the actual key)"""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    scopes: List[str] = Field(..., description="Permission scopes")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp (ISO)")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp (ISO)")
    created_at: str = Field(..., description="Created timestamp (ISO)")
    revoked_at: Optional[str] = Field(None, description="Revoked timestamp (ISO)")
    is_active: bool = Field(..., description="Whether key is active")


class CreateApiKeyResponse(BaseModel):
    """Response for API key creation"""
    api_key: str = Field(..., description="The API key (SHOWN ONLY ONCE!)")
    key_info: ApiKeyResponse = Field(..., description="API key metadata")
    message: str = Field(default="API key created successfully. Save it now, it won't be shown again!")
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "ask_1234567890abcdef...",
                "key_info": {
                    "id": "uuid",
                    "name": "My Integration",
                    "scopes": ["read:user"],
                    "created_at": "2025-01-31T12:00:00Z",
                    "is_active": True
                },
                "message": "API key created successfully. Save it now, it won't be shown again!"
            }
        }


class ListApiKeysResponse(BaseModel):
    """Response for list API keys"""
    api_keys: List[ApiKeyResponse] = Field(..., description="List of API keys")
    total: int = Field(..., description="Total number of keys")


class RevokeApiKeyResponse(BaseModel):
    """Response for API key revoke"""
    success: bool = Field(..., description="API key revoked")
    message: str = Field(default="API key revoked successfully")

