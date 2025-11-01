"""
MFA Login Request DTOs
"""
from pydantic import BaseModel, Field
from typing import Optional


class MFALoginRequest(BaseModel):
    """Request to complete login with MFA"""
    user_id: str = Field(..., description="User ID from initial login")
    client_id: str = Field(..., description="Client ID")
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit TOTP code")
    backup_code: Optional[str] = Field(None, description="Backup code (format: XXXX-XXXX-XXXX)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-uuid",
                "client_id": "client-uuid",
                "totp_code": "123456"
            }
        }

