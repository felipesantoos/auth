"""
MFA Response DTOs
"""
from pydantic import BaseModel, Field
from typing import List


class SetupMFAResponse(BaseModel):
    """Response for MFA setup"""
    secret: str = Field(..., description="TOTP secret (save this!)")
    qr_code: str = Field(..., description="QR code as base64 data URI")
    backup_codes: List[str] = Field(..., description="Backup codes (save these!)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code": "data:image/png;base64,iVBORw0KGgo...",
                "backup_codes": [
                    "1234-5678-9012",
                    "2345-6789-0123",
                ]
            }
        }


class EnableMFAResponse(BaseModel):
    """Response for MFA enable"""
    success: bool = Field(..., description="MFA enabled successfully")
    message: str = Field(default="MFA enabled successfully")


class MFAStatusResponse(BaseModel):
    """Response for MFA status"""
    mfa_enabled: bool = Field(..., description="Whether MFA is enabled")
    backup_codes_remaining: int = Field(..., description="Number of unused backup codes")


class RegenerateBackupCodesResponse(BaseModel):
    """Response for backup codes regeneration"""
    backup_codes: List[str] = Field(..., description="New backup codes")
    message: str = Field(default="Backup codes regenerated successfully")

