"""
Bulk Operation Response DTOs
Models for bulk operation results with success/error tracking
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class BulkOperationError(BaseModel):
    """Error details for a failed item in bulk operation."""
    
    index: int = Field(..., description="Index of the failed item in the request array")
    identifier: Optional[str] = Field(None, description="Item identifier (email, ID, etc.)")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "index": 5,
                "identifier": "user@example.com",
                "error_code": "EMAIL_ALREADY_EXISTS",
                "error_message": "Email already exists in the system",
                "details": {"existing_user_id": "user_xyz789"}
            }
        }


class BulkOperationResponse(BaseModel):
    """Response for bulk operations with detailed success/failure tracking."""
    
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    total: int = Field(..., description="Total operations attempted")
    
    successful_ids: List[str] = Field(
        default_factory=list,
        description="IDs of successfully processed items"
    )
    
    errors: List[BulkOperationError] = Field(
        default_factory=list,
        description="Errors for failed items"
    )
    
    partial_success: bool = Field(
        ...,
        description="True if some operations succeeded and some failed"
    )
    
    processing_time_ms: Optional[int] = Field(
        None,
        description="Total processing time in milliseconds"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success_count": 95,
                "error_count": 5,
                "total": 100,
                "successful_ids": [
                    "user_001",
                    "user_002",
                    "user_003"
                ],
                "errors": [
                    {
                        "index": 10,
                        "identifier": "duplicate@example.com",
                        "error_code": "EMAIL_ALREADY_EXISTS",
                        "error_message": "Email already exists",
                        "details": None
                    },
                    {
                        "index": 25,
                        "identifier": "invalid@test",
                        "error_code": "VALIDATION_ERROR",
                        "error_message": "Invalid email format",
                        "details": None
                    }
                ],
                "partial_success": True,
                "processing_time_ms": 1250,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class BulkCreateUsersResponse(BulkOperationResponse):
    """Response for bulk user creation."""
    pass


class BulkUpdateUsersResponse(BulkOperationResponse):
    """Response for bulk user update."""
    pass


class BulkDeleteUsersResponse(BulkOperationResponse):
    """Response for bulk user deletion."""
    pass

