"""
Workspace Client Database Model
SQLAlchemy model for PostgreSQL persistence
Represents workspace access to clients/applications
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBWorkspaceClient(Base):
    """
    SQLAlchemy model for workspace-client access persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    
    Represents the N:M relationship between Workspace and Client.
    When a workspace has access to a client, all active members inherit that access.
    """
    __tablename__ = "workspace_client"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    workspace_id = Column(String, ForeignKey("workspace.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
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
    workspace = relationship("DBWorkspace", backref="client_accesses")
    client = relationship("DBClient", backref="workspace_accesses")
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraint: a workspace can only have one access record per client
        UniqueConstraint('workspace_id', 'client_id', name='uq_workspace_client'),
        # Composite indexes for queries
        Index('idx_workspace_client_workspace', 'workspace_id'),
        Index('idx_workspace_client_client', 'client_id'),
        Index('idx_workspace_client_active', 'workspace_id', 'active'),
    )

