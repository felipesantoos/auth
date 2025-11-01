"""
User Session Database Model
SQLAlchemy model for tracking user sessions across devices
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBUserSession(Base):
    """
    SQLAlchemy model for user sessions.
    
    Tracks active sessions across multiple devices for security and management.
    """
    __tablename__ = "user_session"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # Token reference (hashed)
    refresh_token_hash = Column(String(255), nullable=False, unique=True)
    
    # Device information
    device_name = Column(String(200), nullable=True)
    device_type = Column(String(50), nullable=True)  # 'mobile', 'desktop', 'tablet', 'unknown'
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)  # "City, Country"
    
    # Activity tracking
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Lifecycle timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    user = relationship("DBAppUser", backref="sessions")
    client = relationship("DBClient")

