"""
App User Database Model
SQLAlchemy model for PostgreSQL persistence
Adapted for multi-tenant architecture with client_id
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBAppUser(Base):
    """
    SQLAlchemy model for PostgreSQL persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    
    Multi-tenant: Each user belongs to a client (tenant).
    """
    __tablename__ = "app_user"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Authentication fields
    username = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User information
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default='user', index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Multi-tenant: Foreign key to client
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    client = relationship("DBClient", backref="users")

