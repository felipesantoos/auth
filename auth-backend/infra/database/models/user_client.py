"""
User Client Database Model
SQLAlchemy model for PostgreSQL persistence
Represents direct user access to clients/applications
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBUserClient(Base):
    """
    SQLAlchemy model for user-client access persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    
    Represents the N:M relationship between User and Client (direct access).
    """
    __tablename__ = "user_client"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspace.id"), nullable=True, index=True)  # Optional context
    
    # Access information
    active = Column(Boolean, default=True, nullable=False, index=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("DBAppUser", backref="client_accesses")
    client = relationship("DBClient", backref="user_accesses")
    workspace = relationship("DBWorkspace", backref="user_client_grants")
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraint: a user can only have one access record per client
        UniqueConstraint('user_id', 'client_id', name='uq_user_client'),
        # Composite indexes for queries
        Index('idx_user_client_user', 'user_id'),
        Index('idx_user_client_client', 'client_id'),
        Index('idx_user_client_active', 'user_id', 'active'),
    )

