"""
Email Verification Request DTOs
"""
from pydantic import BaseModel, Field


class VerifyEmailRequest(BaseModel):
    """Request to verify email"""
    user_id: str = Field(..., description="User ID")
    token: str = Field(..., description="Verification token from email")


class ResendVerificationRequest(BaseModel):
    """Request to resend verification email (no body needed if using auth token)"""
    pass

