"""
MFA Request DTOs
"""
from pydantic import BaseModel, Field
from typing import List


class SetupMFARequest(BaseModel):
    """Request to setup MFA (no body needed, uses auth token)"""
    pass


class EnableMFARequest(BaseModel):
    """Request to enable MFA after setup"""
    secret: str = Field(..., description="TOTP secret from setup")
    totp_code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    backup_codes: List[str] = Field(..., min_items=10, max_items=10, description="Backup codes from setup")


class VerifyTOTPRequest(BaseModel):
    """Request to verify TOTP code"""
    totp_code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class VerifyBackupCodeRequest(BaseModel):
    """Request to verify backup code"""
    backup_code: str = Field(..., description="Backup code (format: XXXX-XXXX-XXXX)")


class DisableMFARequest(BaseModel):
    """Request to disable MFA"""
    password: str = Field(..., description="User password for confirmation")


class RegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes (no body needed)"""
    pass

