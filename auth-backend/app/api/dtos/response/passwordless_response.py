"""
Passwordless Auth Response DTOs
"""
from pydantic import BaseModel, Field


class SendMagicLinkResponse(BaseModel):
    """Response for send magic link"""
    success: bool = Field(..., description="Magic link sent")
    message: str = Field(default="Magic link sent to your email. Check your inbox!")


class VerifyMagicLinkResponse(BaseModel):
    """Response for magic link verification (returns auth tokens)"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    user: dict = Field(..., description="User information")

