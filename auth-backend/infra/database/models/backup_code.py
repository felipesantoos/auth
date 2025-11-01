"""
Backup Code Database Model
SQLAlchemy model for MFA backup codes
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBBackupCode(Base):
    """
    SQLAlchemy model for MFA backup codes.
    
    Backup codes are single-use recovery codes for 2FA.
    """
    __tablename__ = "backup_code"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # Code (hashed)
    code_hash = Column(String(255), nullable=False)
    
    # Usage tracking
    used = Column(Boolean, default=False, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("DBAppUser", backref="backup_codes")
    client = relationship("DBClient")

