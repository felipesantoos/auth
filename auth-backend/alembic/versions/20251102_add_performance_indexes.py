"""add performance indexes

Revision ID: 20251102_perf_idx
Revises: 20251101_1848
Create Date: 2025-11-02 00:00:00

Performance optimization: Add composite indexes for frequently queried columns
Based on performance optimization guide recommendations.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251102_perf_idx'
down_revision: Union[str, None] = '20251101_1848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes to app_user, user_session, and audit_log tables."""
    
    # ===== APP_USER Indexes =====
    # Composite index for multi-tenant queries with active filter
    op.create_index(
        'idx_app_user_client_active',
        'app_user',
        ['client_id', 'is_active'],
        unique=False
    )
    
    # Composite index for multi-tenant queries with role filter
    op.create_index(
        'idx_app_user_client_role',
        'app_user',
        ['client_id', 'role'],
        unique=False
    )
    
    # Index for email verification queries
    op.create_index(
        'idx_app_user_email_verified',
        'app_user',
        ['email_verified'],
        unique=False
    )
    
    # Unique composite index for email per tenant (multi-tenant uniqueness)
    # Note: This enforces that emails are unique within each client/tenant
    op.create_index(
        'idx_app_user_client_email_unique',
        'app_user',
        ['client_id', 'email'],
        unique=True
    )
    
    # Composite index for username searches within tenant
    op.create_index(
        'idx_app_user_client_username',
        'app_user',
        ['client_id', 'username'],
        unique=False
    )
    
    # ===== USER_SESSION Additional Indexes =====
    # Note: user_session already has good indexes, but we can add a few more
    
    # Composite index for active sessions per client
    op.create_index(
        'idx_session_client_active',
        'user_session',
        ['client_id', 'revoked_at', 'expires_at'],
        unique=False
    )
    
    # Index for cleanup of expired sessions
    op.create_index(
        'idx_session_expires_revoked',
        'user_session',
        ['expires_at', 'revoked_at'],
        unique=False
    )
    
    # ===== AUDIT_LOG Additional Indexes =====
    # Note: audit_log already has many indexes, adding a few strategic ones
    
    # Composite index for client + category + date (reporting queries)
    op.create_index(
        'idx_audit_client_category_date',
        'audit_log',
        ['client_id', 'event_category', 'created_at'],
        unique=False
    )
    
    # Composite index for user + success + date (user security monitoring)
    op.create_index(
        'idx_audit_user_success_date',
        'audit_log',
        ['user_id', 'success', 'created_at'],
        unique=False
    )
    
    # Index on status for filtering (beyond just success boolean)
    op.create_index(
        'idx_audit_status',
        'audit_log',
        ['status'],
        unique=False
    )


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Remove audit_log indexes
    op.drop_index('idx_audit_status', table_name='audit_log')
    op.drop_index('idx_audit_user_success_date', table_name='audit_log')
    op.drop_index('idx_audit_client_category_date', table_name='audit_log')
    
    # Remove user_session indexes
    op.drop_index('idx_session_expires_revoked', table_name='user_session')
    op.drop_index('idx_session_client_active', table_name='user_session')
    
    # Remove app_user indexes
    op.drop_index('idx_app_user_client_username', table_name='app_user')
    op.drop_index('idx_app_user_client_email_unique', table_name='app_user')
    op.drop_index('idx_app_user_email_verified', table_name='app_user')
    op.drop_index('idx_app_user_client_role', table_name='app_user')
    op.drop_index('idx_app_user_client_active', table_name='app_user')

