"""
Async Task Database Model
SQLAlchemy model for async_tasks table
"""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, Index
from sqlalchemy.sql import func
from infra.database.database import Base
from datetime import datetime


class DBAsyncTask(Base):
    """
    Database model for async tasks.
    
    Tracks long-running operations that return 202 Accepted.
    Clients poll GET /api/v1/tasks/{id} to check status.
    """
    __tablename__ = "async_tasks"
    
    # Primary Key
    id = Column(String(36), primary_key=True, index=True)
    
    # Task Information
    task_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of task (e.g., bulk_create_users, bulk_delete_users, export_data)"
    )
    
    # Status (pending, processing, completed, failed, cancelled)
    status = Column(
        String(20),
        nullable=False,
        index=True,
        default="pending",
        comment="Current task status"
    )
    
    # Data
    payload = Column(
        JSON,
        nullable=True,
        comment="Input data for the task (JSON)"
    )
    
    result = Column(
        JSON,
        nullable=True,
        comment="Result data if task completed successfully (JSON)"
    )
    
    error = Column(
        Text,
        nullable=True,
        comment="Error message if task failed"
    )
    
    # Progress Tracking
    progress_percentage = Column(
        Integer,
        nullable=True,
        default=0,
        comment="Progress percentage (0-100)"
    )
    
    progress_message = Column(
        String(500),
        nullable=True,
        comment="Current progress message"
    )
    
    # Multi-tenant
    client_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="Client (tenant) ID for isolation"
    )
    
    # Audit
    created_by = Column(
        String(36),
        nullable=False,
        index=True,
        comment="User ID who created the task"
    )
    
    # Celery Integration
    celery_task_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Celery task ID for tracking/cancellation"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        comment="When task was created"
    )
    
    started_at = Column(
        DateTime,
        nullable=True,
        comment="When task processing started"
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="When task completed (success or failure)"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_async_tasks_client_created_by", "client_id", "created_by"),
        Index("ix_async_tasks_status_created_at", "status", "created_at"),
        Index("ix_async_tasks_task_type_status", "task_type", "status"),
        {"comment": "Async tasks for long-running operations (202 Accepted pattern)"}
    )
    
    def __repr__(self):
        return f"<DBAsyncTask(id={self.id}, type={self.task_type}, status={self.status})>"

