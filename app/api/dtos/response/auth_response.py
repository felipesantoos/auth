"""
Authentication Response DTOs
Pydantic models for API responses
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserResponse(BaseModel):
    """Response DTO for user data"""
    id: str
    username: str
    email: EmailStr
    name: str
    role: str
    active: bool
    client_id: Optional[str] = None  # Multi-tenant: client (tenant) ID
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response DTO for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str

