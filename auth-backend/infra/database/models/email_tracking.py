"""
Email Tracking Database Model
SQLAlchemy model for email delivery and engagement tracking
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBEmailTracking(Base):
    """
    SQLAlchemy model for email tracking.
    
    Tracks email delivery, opens, clicks, bounces, and other engagement metrics.
    """
    __tablename__ = "email_tracking"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Unique message identifier
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Foreign keys (user_id can be null for non-authenticated emails)
    user_id = Column(String, ForeignKey("app_user.id"), nullable=True, index=True)
    
    # Email details
    email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    template_name = Column(String(100), nullable=True, index=True)
    
    # Delivery tracking
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Engagement tracking
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0, nullable=False)
    first_click_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0, nullable=False)
    
    # Failure tracking
    bounced = Column(Boolean, default=False, nullable=False)
    bounce_type = Column(String(20), nullable=True)  # 'hard', 'soft'
    bounce_reason = Column(String(500), nullable=True)
    spam_complaint = Column(Boolean, default=False, nullable=False)
    
    # Provider info
    provider = Column(String(50), nullable=True)  # 'smtp', 'sendgrid', 'ses', 'mailgun'
    
    # Metadata
    tags = Column(JSONB, nullable=True)  # ['transactional', 'password-reset']
    metadata = Column(JSONB, nullable=True)  # Additional tracking data
    
    # Relationships
    user = relationship("DBAppUser", backref="email_tracking")
    clicks = relationship("DBEmailClick", back_populates="tracking", cascade="all, delete-orphan")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_email_tracking_user_sent', 'user_id', 'sent_at'),
        Index('idx_email_tracking_email_sent', 'email', 'sent_at'),
        Index('idx_email_tracking_template_sent', 'template_name', 'sent_at'),
    )

