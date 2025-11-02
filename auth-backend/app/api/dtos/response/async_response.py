"""
Async Operation Response DTOs
Models for 202 Accepted pattern and task status
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task status enum for API responses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncOperationResponse(BaseModel):
    """
    Response for async operations (202 Accepted).
    
    Returned when operation is accepted for background processing.
    Client should poll status_url to check progress.
    """
    task_id: str = Field(..., description="Unique task ID")
    status: str = Field(default="processing", description="Initial task status")
    status_url: str = Field(..., description="URL to check task status")
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated completion time (if known)"
    )
    message: str = Field(
        default="Request accepted for processing",
        description="Human-readable message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "processing",
                "status_url": "/api/v1/tasks/task_abc123",
                "estimated_completion": "2024-01-15T10:35:00Z",
                "message": "Request accepted for processing"
            }
        }


class TaskStatusResponse(BaseModel):
    """
    Response with detailed task status.
    
    Used by GET /api/v1/tasks/{task_id} endpoint.
    """
    task_id: str = Field(..., description="Unique task ID")
    task_type: str = Field(..., description="Type of task")
    status: TaskStatusEnum = Field(..., description="Current task status")
    
    # Result or error
    result: Optional[dict] = Field(None, description="Result data if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Progress
    progress_percentage: Optional[int] = Field(
        None,
        description="Progress percentage (0-100)"
    )
    progress_message: Optional[str] = Field(
        None,
        description="Current progress message"
    )
    
    # Metadata
    created_by: str = Field(..., description="User who created the task")
    
    # Timestamps
    created_at: datetime = Field(..., description="When task was created")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When task finished")
    
    # Computed
    duration_seconds: Optional[float] = Field(
        None,
        description="Task duration in seconds (if completed)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "task_type": "bulk_create_users",
                "status": "completed",
                "result": {
                    "success_count": 95,
                    "error_count": 5,
                    "total": 100
                },
                "error": None,
                "progress_percentage": 100,
                "progress_message": "Completed",
                "created_by": "admin_123",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": "2024-01-15T10:32:15Z",
                "duration_seconds": 130.5
            }
        }


class TaskListResponse(BaseModel):
    """Response with list of tasks."""
    tasks: list[TaskStatusResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [],
                "total": 10
            }
        }

