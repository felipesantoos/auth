"""Workspace Response DTOs"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceResponse(BaseModel):
    """Workspace response"""
    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(None, description="Workspace description")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Workspace settings")
    active: bool = Field(..., description="Whether workspace is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "My Company",
                "slug": "my-company",
                "description": "Main company workspace",
                "settings": {},
                "active": True,
                "created_at": "2025-11-03T10:00:00Z",
                "updated_at": "2025-11-03T10:00:00Z"
            }
        }


class WorkspaceMemberResponse(BaseModel):
    """Workspace member response"""
    id: str = Field(..., description="Member ID")
    user_id: str = Field(..., description="User ID")
    workspace_id: str = Field(..., description="Workspace ID")
    role: str = Field(..., description="Member role")
    active: bool = Field(..., description="Whether membership is active")
    invited_at: Optional[datetime] = Field(None, description="Invitation timestamp")
    joined_at: Optional[datetime] = Field(None, description="Join timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "workspace_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "admin",
                "active": True,
                "invited_at": "2025-11-03T10:00:00Z",
                "joined_at": "2025-11-03T10:00:00Z",
                "created_at": "2025-11-03T10:00:00Z",
                "updated_at": "2025-11-03T10:00:00Z"
            }
        }


class WorkspaceListResponse(BaseModel):
    """List of workspaces"""
    workspaces: List[WorkspaceResponse] = Field(..., description="List of workspaces")
    total: int = Field(..., description="Total number of workspaces")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workspaces": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "My Company",
                        "slug": "my-company",
                        "description": "Main workspace",
                        "settings": {},
                        "active": True,
                        "created_at": "2025-11-03T10:00:00Z",
                        "updated_at": "2025-11-03T10:00:00Z"
                    }
                ],
                "total": 1
            }
        }


class WorkspaceMemberListResponse(BaseModel):
    """List of workspace members"""
    members: List[WorkspaceMemberResponse] = Field(..., description="List of members")
    total: int = Field(..., description="Total number of members")
    
    class Config:
        json_schema_extra = {
            "example": {
                "members": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": "123e4567-e89b-12d3-a456-426614174002",
                        "workspace_id": "123e4567-e89b-12d3-a456-426614174000",
                        "role": "admin",
                        "active": True,
                        "joined_at": "2025-11-03T10:00:00Z",
                        "created_at": "2025-11-03T10:00:00Z",
                        "updated_at": "2025-11-03T10:00:00Z"
                    }
                ],
                "total": 1
            }
        }

