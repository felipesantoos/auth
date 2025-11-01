"""
File Database Model
SQLAlchemy model for file metadata persistence
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBFile(Base):
    """
    SQLAlchemy model for file metadata.
    
    Stores information about uploaded files.
    """
    __tablename__ = "files"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Owner
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=True, index=True)  # Multi-tenant
    
    # File information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Storage path/key
    file_size = Column(Integer, nullable=False)  # Bytes
    mime_type = Column(String(100), nullable=False, index=True)
    checksum = Column(String(64), nullable=False, index=True)  # SHA256
    
    # Storage
    storage_provider = Column(String(50), nullable=False)  # local, s3, etc
    public_url = Column(String(1000), nullable=True)
    cdn_url = Column(String(1000), nullable=True)
    
    # Access control
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Organization
    tags = Column(JSON, default=list)  # List of tags
    metadata = Column(JSON, default=dict)  # Custom metadata
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("DBAppUser", backref="files")
    client = relationship("DBClient", backref="files")

