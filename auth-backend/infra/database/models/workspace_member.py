"""
Workspace Member Database Model
SQLAlchemy model for PostgreSQL persistence
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBWorkspaceMember(Base):
    """
    SQLAlchemy model for workspace member persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    
    Represents the N:M relationship between User and Workspace.
    """
    __tablename__ = "workspace_member"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    workspace_id = Column(String, ForeignKey("workspace.id"), nullable=False, index=True)
    
    # Member information
    role = Column(String(50), nullable=False, index=True)  # admin, manager, user
    active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    invited_at = Column(DateTime, nullable=True)
    joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("DBAppUser", backref="workspace_memberships")
    workspace = relationship("DBWorkspace", backref="members")
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraint: a user can only be a member once per workspace
        UniqueConstraint('user_id', 'workspace_id', name='uq_user_workspace'),
        # Composite index for queries
        Index('idx_workspace_member_user', 'user_id'),
        Index('idx_workspace_member_workspace', 'workspace_id'),
        Index('idx_workspace_member_active', 'workspace_id', 'active'),
    )

