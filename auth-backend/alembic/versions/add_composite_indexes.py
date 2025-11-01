"""add composite indexes for performance

Revision ID: composite_indexes_001
Revises: 
Create Date: 2024-11-01

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'composite_indexes_001'
down_revision = None  # Set this to your latest migration ID if needed
branch_labels = None
depends_on = None


def upgrade():
    """Add composite indexes for query optimization"""
    
    # App User composite indexes
    op.create_index(
        'idx_user_client_active',
        'app_user',
        ['client_id', 'is_active'],
        unique=False
    )
    op.create_index(
        'idx_user_email_active',
        'app_user',
        ['email', 'is_active'],
        unique=False
    )
    op.create_index(
        'idx_user_client_username',
        'app_user',
        ['client_id', 'username'],
        unique=False
    )
    op.create_index(
        'idx_user_client_created',
        'app_user',
        ['client_id', 'created_at'],
        unique=False
    )
    
    # User Session composite indexes
    op.create_index(
        'idx_session_user_active',
        'user_session',
        ['user_id', 'revoked_at', 'expires_at'],
        unique=False
    )
    op.create_index(
        'idx_session_client_user',
        'user_session',
        ['client_id', 'user_id'],
        unique=False
    )
    op.create_index(
        'idx_session_user_activity',
        'user_session',
        ['user_id', 'last_activity'],
        unique=False
    )
    
    # Audit Log composite indexes (add new ones, existing ones should already be there)
    op.create_index(
        'idx_audit_user_created',
        'audit_log',
        ['user_id', 'created_at'],
        unique=False,
        if_not_exists=True
    )
    op.create_index(
        'idx_audit_client_created',
        'audit_log',
        ['client_id', 'created_at'],
        unique=False,
        if_not_exists=True
    )


def downgrade():
    """Remove composite indexes"""
    
    # App User indexes
    op.drop_index('idx_user_client_active', table_name='app_user')
    op.drop_index('idx_user_email_active', table_name='app_user')
    op.drop_index('idx_user_client_username', table_name='app_user')
    op.drop_index('idx_user_client_created', table_name='app_user')
    
    # User Session indexes
    op.drop_index('idx_session_user_active', table_name='user_session')
    op.drop_index('idx_session_client_user', table_name='user_session')
    op.drop_index('idx_session_user_activity', table_name='user_session')
    
    # Audit Log indexes
    op.drop_index('idx_audit_user_created', table_name='audit_log', if_exists=True)
    op.drop_index('idx_audit_client_created', table_name='audit_log', if_exists=True)

