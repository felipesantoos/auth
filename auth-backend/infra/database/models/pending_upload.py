"""
Pending Upload Database Model
Tracks presigned URL uploads
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from infra.database.database import Base
import uuid


class DBPendingUpload(Base):
    """
    SQLAlchemy model for pending uploads (presigned URLs).
    
    Tracks uploads that were initiated with presigned URL
    but not yet completed.
    """
    __tablename__ = "pending_uploads"
    
    upload_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

