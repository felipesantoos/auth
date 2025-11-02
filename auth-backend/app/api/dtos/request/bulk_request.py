"""
Bulk Operation Request DTOs
Models for bulk create, update, and delete operations
"""
from pydantic import BaseModel, Field, field_validator
from typing import List
from app.api.dtos.request.auth_request import RegisterRequest, UpdateUserRequest


class BulkCreateUsersRequest(BaseModel):
    """Request model for bulk creating users."""
    
    users: List[RegisterRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of users to create (max 100 per request)"
    )
    
    @field_validator("users")
    @classmethod
    def validate_unique_emails(cls, v):
        """Ensure all emails are unique within the request."""
        emails = [user.email for user in v]
        if len(emails) != len(set(emails)):
            raise ValueError("Duplicate emails found in bulk create request")
        return v
    
    @field_validator("users")
    @classmethod
    def validate_unique_usernames(cls, v):
        """Ensure all usernames are unique within the request."""
        usernames = [user.username for user in v]
        if len(usernames) != len(set(usernames)):
            raise ValueError("Duplicate usernames found in bulk create request")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "username": "user1",
                        "email": "user1@example.com",
                        "password": "SecurePass123",
                        "name": "User One",
                        "client_id": "client_123"
                    },
                    {
                        "username": "user2",
                        "email": "user2@example.com",
                        "password": "SecurePass456",
                        "name": "User Two",
                        "client_id": "client_123"
                    }
                ]
            }
        }


class BulkUpdateUsersRequest(BaseModel):
    """Request model for bulk updating users."""
    
    updates: List[dict] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of user updates with user_id and fields to update (max 100)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {
                        "user_id": "user_abc123",
                        "is_active": False,
                        "role": "user"
                    },
                    {
                        "user_id": "user_def456",
                        "name": "Updated Name",
                        "email": "newemail@example.com"
                    }
                ]
            }
        }


class BulkDeleteUsersRequest(BaseModel):
    """Request model for bulk deleting users."""
    
    user_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of user IDs to delete (max 100)"
    )
    
    @field_validator("user_ids")
    @classmethod
    def validate_unique_ids(cls, v):
        """Ensure all IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate user IDs found in bulk delete request")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_ids": [
                    "user_abc123",
                    "user_def456",
                    "user_ghi789"
                ]
            }
        }

