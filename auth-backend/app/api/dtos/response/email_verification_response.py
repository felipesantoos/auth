"""
Email Verification Response DTOs
"""
from pydantic import BaseModel, Field


class VerifyEmailResponse(BaseModel):
    """Response for email verification"""
    success: bool = Field(..., description="Email verified successfully")
    message: str = Field(default="Email verified successfully")


class ResendVerificationResponse(BaseModel):
    """Response for resend verification"""
    success: bool = Field(..., description="Verification email sent")
    message: str = Field(default="Verification email sent successfully")


class EmailVerificationStatusResponse(BaseModel):
    """Response for email verification status"""
    email_verified: bool = Field(..., description="Whether email is verified")

