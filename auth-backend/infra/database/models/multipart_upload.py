"""
Multipart Upload Database Model
Tracks chunked/multipart uploads
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from infra.database.database import Base
import uuid


class DBMultipartUpload(Base):
    """
    SQLAlchemy model for multipart uploads (chunked uploads).
    
    Tracks large file uploads split into multiple parts.
    """
    __tablename__ = "multipart_uploads"
    
    upload_id = Column(String, primary_key=True)  # S3 Upload ID
    file_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default='initiated')  # initiated, uploading, completed, aborted
    total_size = Column(Integer, nullable=True)
    uploaded_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

