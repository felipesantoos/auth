"""
API Key Database Model
SQLAlchemy model for API keys (Personal Access Tokens)
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBApiKey(Base):
    """
    SQLAlchemy model for API keys.
    
    API keys provide programmatic access with fine-grained permissions.
    """
    __tablename__ = "api_key"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # Key details
    name = Column(String(100), nullable=False)  # User-friendly name
    key_hash = Column(String(255), nullable=False, unique=True)  # bcrypt hash
    
    # Permissions
    scopes = Column(ARRAY(String), nullable=False)  # Array of scope strings
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    
    # Lifecycle timestamps
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    user = relationship("DBAppUser", backref="api_keys")
    client = relationship("DBClient")

