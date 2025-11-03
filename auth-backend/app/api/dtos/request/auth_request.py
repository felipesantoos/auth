"""
Authentication Request DTOs
Pydantic models for API request validation
Adapted for multi-tenant architecture
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    """DTO for user login (multi-workspace)"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    client_id: Optional[str] = Field(None, description="[DEPRECATED] Client ID for backwards compatibility")


class RegisterRequest(BaseModel):
    """DTO for user registration (multi-workspace)"""
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: str = Field(..., min_length=2, max_length=255, description="User full name")
    workspace_name: Optional[str] = Field(None, min_length=2, max_length=200, description="Custom workspace name (defaults to '{username}'s Workspace')")
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequest(BaseModel):
    """DTO for password change"""
    old_password: str = Field(..., min_length=6, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


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
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")
    client_id: Optional[str] = Field(None, description="Client (tenant) ID. Can also be provided via X-Client-ID header or subdomain")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password meets strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

