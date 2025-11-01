"""
WebAuthn Credential Database Model
SQLAlchemy model for WebAuthn credentials (Passkeys)
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBWebAuthnCredential(Base):
    """
    SQLAlchemy model for WebAuthn credentials.
    
    WebAuthn provides passwordless authentication using biometrics or security keys.
    """
    __tablename__ = "webauthn_credential"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("app_user.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False, index=True)
    
    # WebAuthn fields
    credential_id = Column(String(255), nullable=False, unique=True, index=True)
    public_key = Column(Text, nullable=False)  # Base64 encoded
    counter = Column(Integer, default=0, nullable=False)  # Sign counter for replay protection
    aaguid = Column(String(36), nullable=True)  # Authenticator AAGUID
    
    # Device information
    device_name = Column(String(200), nullable=True)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    
    # Lifecycle timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    user = relationship("DBAppUser", backref="webauthn_credentials")
    client = relationship("DBClient")

