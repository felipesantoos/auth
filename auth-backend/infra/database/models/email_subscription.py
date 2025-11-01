"""
Email Subscription Database Model
SQLAlchemy model for managing user email preferences and unsubscribe
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBEmailSubscription(Base):
    """
    SQLAlchemy model for email subscription preferences.
    
    Manages user preferences for different types of emails and unsubscribe functionality.
    """
    __tablename__ = "email_subscriptions"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key (can be null for non-registered users)
    user_id = Column(String, ForeignKey("app_user.id"), nullable=True, index=True)
    
    # Email address (indexed for quick lookup)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # Subscription preferences (granular control)
    marketing_emails = Column(Boolean, default=True, nullable=False)
    notification_emails = Column(Boolean, default=True, nullable=False)
    product_updates = Column(Boolean, default=True, nullable=False)
    newsletter = Column(Boolean, default=True, nullable=False)
    
    # Unsubscribe tracking
    unsubscribed_at = Column(DateTime, nullable=True)
    unsubscribe_reason = Column(String(500), nullable=True)
    unsubscribe_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("DBAppUser", backref="email_subscription")

