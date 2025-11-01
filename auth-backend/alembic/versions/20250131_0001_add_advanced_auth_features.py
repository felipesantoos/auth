"""add_advanced_auth_features

Revision ID: 20250131_0001
Revises: 20250101_0002
Create Date: 2025-01-31 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250131_0001'
down_revision: Union[str, None] = '20250101_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration: Add advanced authentication features"""
    
    # 1. Add Email Verification fields to app_user
    op.add_column('app_user', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('app_user', sa.Column('email_verification_token', sa.String(length=255), nullable=True))
    op.add_column('app_user', sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True))
    
    # 2. Add MFA/2FA fields to app_user
    op.add_column('app_user', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('app_user', sa.Column('mfa_secret', sa.String(length=255), nullable=True))
    
    # 3. Add Account Security fields (lockout) to app_user
    op.add_column('app_user', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.add_column('app_user', sa.Column('locked_until', sa.DateTime(), nullable=True))
    
    # 4. Add Passwordless Auth (Magic Links) fields to app_user
    op.add_column('app_user', sa.Column('magic_link_token', sa.String(length=255), nullable=True))
    op.add_column('app_user', sa.Column('magic_link_sent_at', sa.DateTime(), nullable=True))
    
    # 5. Create backup_code table for MFA
    op.create_table(
        'backup_code',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_code_id'), 'backup_code', ['id'], unique=False)
    op.create_index(op.f('ix_backup_code_user_id'), 'backup_code', ['user_id'], unique=False)
    op.create_index(op.f('ix_backup_code_client_id'), 'backup_code', ['client_id'], unique=False)
    op.create_index(op.f('ix_backup_code_used'), 'backup_code', ['used'], unique=False)
    
    # 6. Create user_session table
    op.create_table(
        'user_session',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=False),
        sa.Column('device_name', sa.String(length=200), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('refresh_token_hash')
    )
    op.create_index(op.f('ix_user_session_id'), 'user_session', ['id'], unique=False)
    op.create_index(op.f('ix_user_session_user_id'), 'user_session', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_session_client_id'), 'user_session', ['client_id'], unique=False)
    op.create_index(op.f('ix_user_session_revoked_at'), 'user_session', ['revoked_at'], unique=False)
    op.create_index(op.f('ix_user_session_expires_at'), 'user_session', ['expires_at'], unique=False)
    
    # 7. Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),  # Nullable for unauthenticated events
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='success'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_id'), 'audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_audit_log_user_id'), 'audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_log_client_id'), 'audit_log', ['client_id'], unique=False)
    op.create_index(op.f('ix_audit_log_event_type'), 'audit_log', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_log_created_at'), 'audit_log', ['created_at'], unique=False)
    # Composite indexes for common queries
    op.create_index('idx_audit_user_event', 'audit_log', ['user_id', 'event_type'], unique=False)
    op.create_index('idx_audit_client_event', 'audit_log', ['client_id', 'event_type'], unique=False)
    op.create_index('idx_audit_created', 'audit_log', ['created_at'], unique=False)
    
    # 8. Create api_key table
    op.create_table(
        'api_key',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_key_id'), 'api_key', ['id'], unique=False)
    op.create_index(op.f('ix_api_key_user_id'), 'api_key', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_key_client_id'), 'api_key', ['client_id'], unique=False)
    op.create_index(op.f('ix_api_key_expires_at'), 'api_key', ['expires_at'], unique=False)
    op.create_index(op.f('ix_api_key_revoked_at'), 'api_key', ['revoked_at'], unique=False)
    
    # 9. Create webauthn_credential table
    op.create_table(
        'webauthn_credential',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('credential_id', sa.String(length=255), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('counter', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('aaguid', sa.String(length=36), nullable=True),
        sa.Column('device_name', sa.String(length=200), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credential_id')
    )
    op.create_index(op.f('ix_webauthn_credential_id'), 'webauthn_credential', ['id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_user_id'), 'webauthn_credential', ['user_id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_client_id'), 'webauthn_credential', ['client_id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_credential_id'), 'webauthn_credential', ['credential_id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_revoked_at'), 'webauthn_credential', ['revoked_at'], unique=False)


def downgrade() -> None:
    """Revert migration"""
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_webauthn_credential_revoked_at'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_credential_id'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_client_id'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_user_id'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_id'), table_name='webauthn_credential')
    op.drop_table('webauthn_credential')
    
    op.drop_index(op.f('ix_api_key_revoked_at'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_expires_at'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_client_id'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_user_id'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_id'), table_name='api_key')
    op.drop_table('api_key')
    
    op.drop_index('idx_audit_created', table_name='audit_log')
    op.drop_index('idx_audit_client_event', table_name='audit_log')
    op.drop_index('idx_audit_user_event', table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_created_at'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_event_type'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_client_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_user_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_id'), table_name='audit_log')
    op.drop_table('audit_log')
    
    op.drop_index(op.f('ix_user_session_expires_at'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_revoked_at'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_client_id'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_user_id'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_id'), table_name='user_session')
    op.drop_table('user_session')
    
    op.drop_index(op.f('ix_backup_code_used'), table_name='backup_code')
    op.drop_index(op.f('ix_backup_code_client_id'), table_name='backup_code')
    op.drop_index(op.f('ix_backup_code_user_id'), table_name='backup_code')
    op.drop_index(op.f('ix_backup_code_id'), table_name='backup_code')
    op.drop_table('backup_code')
    
    # Remove columns from app_user
    op.drop_column('app_user', 'magic_link_sent_at')
    op.drop_column('app_user', 'magic_link_token')
    op.drop_column('app_user', 'locked_until')
    op.drop_column('app_user', 'failed_login_attempts')
    op.drop_column('app_user', 'mfa_secret')
    op.drop_column('app_user', 'mfa_enabled')
    op.drop_column('app_user', 'email_verification_sent_at')
    op.drop_column('app_user', 'email_verification_token')
    op.drop_column('app_user', 'email_verified')

