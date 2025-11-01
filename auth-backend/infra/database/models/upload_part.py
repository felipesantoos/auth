"""
Upload Part Database Model
Tracks individual parts of multipart upload
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBUploadPart(Base):
    """
    SQLAlchemy model for upload parts.
    
    Each part represents a chunk of a multipart upload.
    """
    __tablename__ = "upload_parts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, ForeignKey("multipart_uploads.upload_id"), nullable=False, index=True)
    part_number = Column(Integer, nullable=False)
    etag = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    multipart_upload = relationship("DBMultipartUpload", backref="parts")

