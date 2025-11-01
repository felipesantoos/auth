"""
Passwordless Auth Request DTOs
"""
from pydantic import BaseModel, Field, EmailStr


class SendMagicLinkRequest(BaseModel):
    """Request to send magic link"""
    email: EmailStr = Field(..., description="User email")
    client_id: str = Field(..., description="Client ID")


class VerifyMagicLinkRequest(BaseModel):
    """Request to verify magic link and login"""
    user_id: str = Field(..., description="User ID")
    token: str = Field(..., description="Magic link token")
    client_id: str = Field(..., description="Client ID")

