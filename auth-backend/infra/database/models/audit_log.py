"""
Audit Log Database Model
SQLAlchemy model for security and audit event logging
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBAuditLog(Base):
    """
    SQLAlchemy model for audit logs.
    
    Tracks all security-relevant events for compliance and security analysis.
    """
    __tablename__ = "audit_log"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys (user_id can be null for unauthenticated events)
    user_id = Column(String, ForeignKey("app_user.id"), nullable=True, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)  # 'user', 'session', 'api_key', etc.
    resource_id = Column(String(100), nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Additional data
    metadata = Column(JSONB, nullable=True)  # Event-specific data
    
    # Status
    status = Column(String(20), nullable=False, default='success')  # 'success', 'failure', 'warning'
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("DBAppUser")
    client = relationship("DBClient")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_event', 'user_id', 'event_type'),
        Index('idx_audit_client_event', 'client_id', 'event_type'),
        Index('idx_audit_created', 'created_at'),
    )

