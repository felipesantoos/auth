"""
Workspace Database Model
SQLAlchemy model for PostgreSQL persistence
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from infra.database.database import Base
import uuid


class DBWorkspace(Base):
    """
    SQLAlchemy model for workspace persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    """
    __tablename__ = "workspace"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Workspace information
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    settings = Column(JSONB, nullable=True)
    
    # Status
    active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

