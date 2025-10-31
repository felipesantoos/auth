"""
Client Database Model
SQLAlchemy model for PostgreSQL persistence
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from infra.database.database import Base
import uuid


class DBClient(Base):
    """
    SQLAlchemy model for client (tenant) persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    """
    __tablename__ = "client"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Client information
    name = Column(String(200), nullable=False, index=True)
    subdomain = Column(String(100), nullable=False, unique=True, index=True)
    api_key = Column(String(255), nullable=True, unique=True, index=True)
    
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

