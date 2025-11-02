"""
Async Task Domain Model
Represents an asynchronous operation tracked by the system
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class TaskStatus(str, Enum):
    """
    Status of an async task.
    
    Lifecycle:
    1. PENDING - Task created, waiting to be picked up
    2. PROCESSING - Task is currently being processed
    3. COMPLETED - Task completed successfully
    4. FAILED - Task failed with error
    5. CANCELLED - Task was cancelled by user or system
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    def is_terminal(self) -> bool:
        """Check if status is terminal (won't change)."""
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
    
    def is_active(self) -> bool:
        """Check if task is actively running."""
        return self in (TaskStatus.PENDING, TaskStatus.PROCESSING)


@dataclass
class AsyncTask:
    """
    Domain model for async task.
    
    Represents a long-running operation that returns 202 Accepted.
    Client can poll /api/v1/tasks/{id} to check status.
    
    Example:
        >>> task = AsyncTask(
        ...     task_type="bulk_create_users",
        ...     payload={"users": [...]},
        ...     created_by="admin_123",
        ...     client_id="client_123"
        ... )
        >>> task.start_processing()
        >>> # ... do work ...
        >>> task.complete(result={"success_count": 100})
    """
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Task type (e.g., "bulk_create_users", "bulk_delete_users", "export_data")
    task_type: str = field(default="")
    
    # Status
    status: TaskStatus = field(default=TaskStatus.PENDING)
    
    # Input/Output
    payload: Optional[dict] = field(default=None)  # Input data
    result: Optional[dict] = field(default=None)   # Success result
    error: Optional[str] = field(default=None)     # Error message if failed
    
    # Metadata
    created_by: str = field(default="")           # User ID who created task
    client_id: str = field(default="")            # Tenant isolation
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    
    # Progress tracking (optional)
    progress_percentage: Optional[int] = field(default=0)  # 0-100
    progress_message: Optional[str] = field(default=None)
    
    # Celery task ID (for cancellation)
    celery_task_id: Optional[str] = field(default=None)
    
    def start_processing(self):
        """Mark task as processing."""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.PROCESSING
            self.started_at = datetime.utcnow()
    
    def complete(self, result: dict):
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100
    
    def fail(self, error: str):
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
    
    def cancel(self):
        """Mark task as cancelled."""
        if not self.status.is_terminal():
            self.status = TaskStatus.CANCELLED
            self.completed_at = datetime.utcnow()
    
    def update_progress(self, percentage: int, message: Optional[str] = None):
        """
        Update task progress.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Optional progress message
        """
        self.progress_percentage = max(0, min(100, percentage))
        if message:
            self.progress_message = message
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get task duration in seconds (if completed)."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "status": self.status.value,
            "payload": self.payload,
            "result": self.result,
            "error": self.error,
            "created_by": self.created_by,
            "client_id": self.client_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percentage": self.progress_percentage,
            "progress_message": self.progress_message,
            "duration_seconds": self.get_duration_seconds()
        }

