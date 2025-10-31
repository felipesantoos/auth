"""
Authentication Request DTOs
Pydantic models for API request validation
Adapted for multi-tenant architecture
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """DTO for user login (multi-tenant)"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    client_id: Optional[str] = Field(None, description="Client (tenant) ID. Can also be provided via X-Client-ID header or subdomain")


class RegisterRequest(BaseModel):
    """DTO for user registration (multi-tenant)"""
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    name: str = Field(..., min_length=2, max_length=255, description="User full name")
    client_id: Optional[str] = Field(None, description="Client (tenant) ID. Can also be provided via X-Client-ID header or subdomain")


class ChangePasswordRequest(BaseModel):
    """DTO for password change"""
    old_password: str = Field(..., min_length=6, description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")


class RefreshTokenRequest(BaseModel):
    """DTO for token refresh"""
    refresh_token: str = Field(..., description="Refresh token")


class UpdateUserRequest(BaseModel):
    """DTO for user update"""
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="Full name")
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Active status")


class ForgotPasswordRequest(BaseModel):
    """DTO for password reset request (multi-tenant)"""
    email: EmailStr = Field(..., description="User email address")
    client_id: Optional[str] = Field(None, description="Client (tenant) ID. Can also be provided via X-Client-ID header or subdomain")


class ResetPasswordRequest(BaseModel):
    """DTO for password reset with token (multi-tenant)"""
    reset_token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=6, description="New password")
    client_id: Optional[str] = Field(None, description="Client (tenant) ID. Can also be provided via X-Client-ID header or subdomain")

