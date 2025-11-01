"""
Email Click Database Model
SQLAlchemy model for tracking individual email link clicks
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBEmailClick(Base):
    """
    SQLAlchemy model for email click tracking.
    
    Records each individual click on links within tracked emails.
    """
    __tablename__ = "email_clicks"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to email tracking
    tracking_id = Column(String, ForeignKey("email_tracking.id"), nullable=False, index=True)
    
    # Click details
    url = Column(Text, nullable=False)
    clicked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # User context
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    tracking = relationship("DBEmailTracking", back_populates="clicks")

