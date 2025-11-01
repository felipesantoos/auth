"""
File Share Database Model
Tracks file sharing permissions
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBFileShare(Base):
    """
    SQLAlchemy model for file sharing.
    
    Represents permission granted to a user to access another user's file.
    """
    __tablename__ = "file_shares"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, ForeignKey("files.id"), nullable=False, index=True)
    shared_by = Column(String, ForeignKey("app_user.id"), nullable=False)
    shared_with = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    permission = Column(String(20), nullable=False, default='read')  # read, write
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship("DBFile", backref="shares")

