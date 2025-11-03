"""Workspace Request DTOs"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class WorkspaceCreateRequest(BaseModel):
    """Request to create a new workspace"""
    name: str = Field(..., min_length=2, max_length=200, description="Workspace name")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Workspace settings")
    
    @validator('slug')
    def validate_slug(cls, v):
        if v:
            # Slug must be lowercase alphanumeric with hyphens/underscores
            if not re.match(r'^[a-z0-9_-]+$', v):
                raise ValueError('Slug can only contain lowercase letters, numbers, hyphens, and underscores')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Company",
                "slug": "my-company",
                "description": "Main company workspace",
                "settings": {}
            }
        }


class WorkspaceUpdateRequest(BaseModel):
    """Request to update a workspace"""
    name: Optional[str] = Field(None, min_length=2, max_length=200, description="Workspace name")
    slug: Optional[str] = Field(None, min_length=2, max_length=100, description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=1000, description="Workspace description")
    settings: Optional[Dict[str, Any]] = Field(None, description="Workspace settings")
    
    @validator('slug')
    def validate_slug(cls, v):
        if v:
            if not re.match(r'^[a-z0-9_-]+$', v):
                raise ValueError('Slug can only contain lowercase letters, numbers, hyphens, and underscores')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Company Name",
                "description": "Updated description"
            }
        }


class AddWorkspaceMemberRequest(BaseModel):
    """Request to add a member to workspace"""
    user_id: str = Field(..., description="User ID to add")
    role: str = Field(..., description="Member role: admin, manager, or user")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'manager', 'user']
        if v.lower() not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "user"
            }
        }


class UpdateMemberRoleRequest(BaseModel):
    """Request to update member role"""
    role: str = Field(..., description="New role: admin, manager, or user")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'manager', 'user']
        if v.lower() not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "manager"
            }
        }

