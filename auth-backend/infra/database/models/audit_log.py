"""
Comprehensive Audit Log Database Model
SQLAlchemy model for PostgreSQL persistence with JSONB and array support
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBAuditLog(Base):
    """
    Comprehensive SQLAlchemy model for audit logs.
    
    Features:
    - JSONB columns for flexible metadata storage
    - Array columns for tags
    - Composite indexes for performance
    - Multi-tenant isolation via client_id
    """
    __tablename__ = "audit_log"
    
    # ===== Identification =====
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    event_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID
    
    # ===== Event Details =====
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=True, index=True)
    action = Column(String(500), nullable=True)  # Human-readable action
    description = Column(Text, nullable=True)  # Detailed description
    
    # ===== Actor (who) =====
    user_id = Column(String, ForeignKey("app_user.id"), nullable=True, index=True)
    username = Column(String(100), nullable=True)
    user_email = Column(String(255), nullable=True)
    impersonated_by = Column(String, nullable=True)  # Admin ID if impersonating
    
    # ===== Multi-tenant =====
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # ===== Resource (what) =====
    resource_type = Column(String(100), nullable=True, index=True)  # "project", "document", etc.
    resource_id = Column(String(100), nullable=True, index=True)
    resource_name = Column(String(500), nullable=True)  # For display
    
    # ===== Context (where, when, how) =====
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)  # Geolocation
    request_id = Column(String(36), nullable=True, index=True)  # Correlation ID
    session_id = Column(String, nullable=True, index=True)
    
    # ===== Changes (before/after) - JSONB for flexible storage =====
    changes = Column(JSONB, nullable=True)  # Array of change objects
    old_values = Column(JSONB, nullable=True)  # Complete old state
    new_values = Column(JSONB, nullable=True)  # Complete new state
    
    # ===== Additional Context =====
    event_metadata = Column(JSONB, nullable=True)  # Event-specific data (flexible)
    tags = Column(ARRAY(String), nullable=True)  # ["sensitive", "compliance", "critical"]
    
    # ===== Status =====
    success = Column(Boolean, default=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default='success', index=True)  # success/failure/warning
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # ===== Timestamps =====
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # ===== Relationships =====
    user = relationship("DBAppUser")
    client = relationship("DBClient")
    
    # ===== Composite Indexes for Performance =====
    __table_args__ = (
        # User activity queries
        Index('idx_audit_user_event', 'user_id', 'event_type'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_user_category', 'user_id', 'event_category'),
        
        # Client activity queries
        Index('idx_audit_client_event', 'client_id', 'event_type'),
        Index('idx_audit_client_created', 'client_id', 'created_at'),
        Index('idx_audit_client_category', 'client_id', 'event_category'),
        
        # Entity history queries
        Index('idx_audit_entity', 'resource_type', 'resource_id', 'created_at'),
        
        # Failed events queries (security monitoring)
        Index('idx_audit_failed', 'success', 'created_at'),
        
        # Category queries (compliance reporting)
        Index('idx_audit_category_created', 'event_category', 'created_at'),
        
        # Request correlation
        Index('idx_audit_request', 'request_id'),
    )
