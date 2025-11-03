"""
App User Database Model
SQLAlchemy model for PostgreSQL persistence
Adapted for multi-tenant architecture with client_id
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, UniqueConstraint
import sqlalchemy as sa
from infra.database.database import Base
import uuid


class DBAppUser(Base):
    """
    SQLAlchemy model for PostgreSQL persistence.
    
    This is an infrastructure detail - adapter for the database.
    Domain layer doesn't know about this.
    
    Multi-workspace: Users have global identity and can belong to multiple workspaces.
    """
    __tablename__ = "app_user"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Authentication fields
    username = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # User information
    full_name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # REMOVED: role (now in workspace_member table)
    # REMOVED: client_id (now via workspace_member or user_client tables)
    
    # Email Verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    
    # MFA/2FA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    
    # Account Security (Brute Force Protection)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Passwordless Auth (Magic Links)
    magic_link_token = Column(String(255), nullable=True)
    magic_link_sent_at = Column(DateTime, nullable=True)
    
    # Avatar / Profile Picture
    avatar_url = Column(String(1000), nullable=True)
    
    # KYC (Know Your Customer) / Identity Verification
    kyc_document_id = Column(String(255), nullable=True)  # Foreign key to files table
    kyc_status = Column(String(50), nullable=True)  # pending, approved, rejected
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships (updated for multi-workspace)
    # REMOVED: client relationship (now via workspace_member or user_client)
    
    # Composite Indexes for query optimization (updated for multi-workspace)
    __table_args__ = (
        # Email must be globally unique
        sa.UniqueConstraint('email', name='uq_user_email'),
    )

