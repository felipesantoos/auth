"""
MFA Login Response DTOs
"""
from pydantic import BaseModel, Field


class MFARequiredResponse(BaseModel):
    """Response when MFA is required"""
    mfa_required: bool = Field(default=True, description="MFA verification required")
    user_id: str = Field(..., description="User ID")
    message: str = Field(default="MFA verification required. Provide TOTP code or backup code.")

