"""initial schema consolidated

Revision ID: initial_consolidated
Revises: None
Create Date: 2025-11-04 00:00:00

Consolidated database schema containing:
- All core tables (client, app_user, permission)
- All auth & security tables (api_key, backup_code, user_session, webauthn_credential)
- All audit tables (audit_log)
- All email tables (email_tracking, email_clicks, email_subscriptions, email_ab_tests, email_ab_variants)
- All file upload tables (files, file_shares, multipart_uploads, pending_uploads, upload_parts)
- Async tasks table for 202 Accepted pattern (async_tasks)
- All performance indexes

Total: 18 tables with optimized indexes for multi-tenant queries.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'initial_consolidated'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all database tables and indexes."""
    
    # ========================================================================
    # CORE TABLES
    # ========================================================================
    
    # CLIENT (Multi-tenant table)
    op.create_table(
        'client',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('subdomain', sa.String(length=100), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_id'), 'client', ['id'], unique=False)
    op.create_index(op.f('ix_client_name'), 'client', ['name'], unique=False)
    op.create_index(op.f('ix_client_subdomain'), 'client', ['subdomain'], unique=True)
    op.create_index(op.f('ix_client_api_key'), 'client', ['api_key'], unique=True)
    op.create_index(op.f('ix_client_active'), 'client', ['active'], unique=False)
    
    # APP_USER (Main user table with all features)
    op.create_table(
        'app_user',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False),
        sa.Column('mfa_secret', sa.String(length=255), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('magic_link_token', sa.String(length=255), nullable=True),
        sa.Column('magic_link_sent_at', sa.DateTime(), nullable=True),
        sa.Column('avatar_url', sa.String(length=1000), nullable=True),
        sa.Column('kyc_document_id', sa.String(length=255), nullable=True),
        sa.Column('kyc_status', sa.String(length=50), nullable=True),
        sa.Column('kyc_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Basic indexes
    op.create_index(op.f('ix_app_user_id'), 'app_user', ['id'], unique=False)
    op.create_index(op.f('ix_app_user_username'), 'app_user', ['username'], unique=False)
    op.create_index(op.f('ix_app_user_email'), 'app_user', ['email'], unique=False)
    op.create_index(op.f('ix_app_user_client_id'), 'app_user', ['client_id'], unique=False)
    op.create_index(op.f('ix_app_user_is_active'), 'app_user', ['is_active'], unique=False)
    op.create_index(op.f('ix_app_user_role'), 'app_user', ['role'], unique=False)
    # Composite indexes
    op.create_index('idx_user_client_active', 'app_user', ['client_id', 'is_active'], unique=False)
    op.create_index('idx_user_client_created', 'app_user', ['client_id', 'created_at'], unique=False)
    op.create_index('idx_user_client_username', 'app_user', ['client_id', 'username'], unique=False)
    op.create_index('idx_user_email_active', 'app_user', ['email', 'is_active'], unique=False)
    # Performance indexes (from 20251102)
    op.create_index('idx_app_user_client_active', 'app_user', ['client_id', 'is_active'], unique=False)
    op.create_index('idx_app_user_client_role', 'app_user', ['client_id', 'role'], unique=False)
    op.create_index('idx_app_user_email_verified', 'app_user', ['email_verified'], unique=False)
    op.create_index('idx_app_user_client_email_unique', 'app_user', ['client_id', 'email'], unique=True)
    op.create_index('idx_app_user_client_username', 'app_user', ['client_id', 'username'], unique=False)
    
    # PERMISSION (Fine-grained access control)
    op.create_table(
        'permission',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('action', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'MANAGE', name='permissionactiondb'), nullable=False),
        sa.Column('granted_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_client_id'), 'permission', ['client_id'], unique=False)
    op.create_index(op.f('ix_permission_user_id'), 'permission', ['user_id'], unique=False)
    
    # ========================================================================
    # AUTH & SECURITY TABLES
    # ========================================================================
    
    # API_KEY
    op.create_table(
        'api_key',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_key_id'), 'api_key', ['id'], unique=False)
    op.create_index(op.f('ix_api_key_user_id'), 'api_key', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_key_client_id'), 'api_key', ['client_id'], unique=False)
    op.create_index(op.f('ix_api_key_expires_at'), 'api_key', ['expires_at'], unique=False)
    op.create_index(op.f('ix_api_key_revoked_at'), 'api_key', ['revoked_at'], unique=False)
    
    # BACKUP_CODE (MFA backup codes)
    op.create_table(
        'backup_code',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_code_id'), 'backup_code', ['id'], unique=False)
    op.create_index(op.f('ix_backup_code_user_id'), 'backup_code', ['user_id'], unique=False)
    op.create_index(op.f('ix_backup_code_client_id'), 'backup_code', ['client_id'], unique=False)
    op.create_index(op.f('ix_backup_code_used'), 'backup_code', ['used'], unique=False)
    
    # USER_SESSION (Multi-device session management)
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
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('refresh_token_hash')
    )
    # Basic indexes
    op.create_index(op.f('ix_user_session_id'), 'user_session', ['id'], unique=False)
    op.create_index(op.f('ix_user_session_user_id'), 'user_session', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_session_client_id'), 'user_session', ['client_id'], unique=False)
    op.create_index(op.f('ix_user_session_expires_at'), 'user_session', ['expires_at'], unique=False)
    op.create_index(op.f('ix_user_session_revoked_at'), 'user_session', ['revoked_at'], unique=False)
    # Composite indexes
    op.create_index('idx_session_client_user', 'user_session', ['client_id', 'user_id'], unique=False)
    op.create_index('idx_session_user_active', 'user_session', ['user_id', 'revoked_at', 'expires_at'], unique=False)
    op.create_index('idx_session_user_activity', 'user_session', ['user_id', 'last_activity'], unique=False)
    # Performance indexes (from 20251102)
    op.create_index('idx_session_client_active', 'user_session', ['client_id', 'revoked_at', 'expires_at'], unique=False)
    op.create_index('idx_session_expires_revoked', 'user_session', ['expires_at', 'revoked_at'], unique=False)
    
    # WEBAUTHN_CREDENTIAL (FIDO2/WebAuthn)
    op.create_table(
        'webauthn_credential',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('credential_id', sa.String(length=255), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('counter', sa.Integer(), nullable=False),
        sa.Column('aaguid', sa.String(length=36), nullable=True),
        sa.Column('device_name', sa.String(length=200), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webauthn_credential_id'), 'webauthn_credential', ['id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_credential_id'), 'webauthn_credential', ['credential_id'], unique=True)
    op.create_index(op.f('ix_webauthn_credential_user_id'), 'webauthn_credential', ['user_id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_client_id'), 'webauthn_credential', ['client_id'], unique=False)
    op.create_index(op.f('ix_webauthn_credential_revoked_at'), 'webauthn_credential', ['revoked_at'], unique=False)
    
    # ========================================================================
    # AUDIT TABLE
    # ========================================================================
    
    # AUDIT_LOG (Compliance & security)
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Basic indexes
    op.create_index(op.f('ix_audit_log_id'), 'audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_audit_log_user_id'), 'audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_log_client_id'), 'audit_log', ['client_id'], unique=False)
    op.create_index(op.f('ix_audit_log_event_type'), 'audit_log', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_log_created_at'), 'audit_log', ['created_at'], unique=False)
    # Composite indexes
    op.create_index('idx_audit_client_created', 'audit_log', ['client_id', 'created_at'], unique=False)
    op.create_index('idx_audit_client_event', 'audit_log', ['client_id', 'event_type'], unique=False)
    op.create_index('idx_audit_user_created', 'audit_log', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_audit_user_event', 'audit_log', ['user_id', 'event_type'], unique=False)
    # Performance indexes (from 20251102) - Note: event_category and success fields may not exist yet
    # op.create_index('idx_audit_client_category_date', 'audit_log', ['client_id', 'event_category', 'created_at'], unique=False)
    # op.create_index('idx_audit_user_success_date', 'audit_log', ['user_id', 'success', 'created_at'], unique=False)
    op.create_index('idx_audit_status', 'audit_log', ['status'], unique=False)
    
    # ========================================================================
    # EMAIL TABLES
    # ========================================================================
    
    # EMAIL_AB_TESTS (A/B testing for emails)
    op.create_table(
        'email_ab_tests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('distribution_type', sa.String(length=20), nullable=False),
        sa.Column('variant_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('winner_variant', sa.String(length=10), nullable=True),
        sa.Column('winner_metric', sa.String(length=20), nullable=True),
        sa.Column('auto_select_winner', sa.String(), nullable=False),
        sa.Column('min_sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('winner_selected_at', sa.DateTime(), nullable=True),
        sa.Column('test_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_ab_tests_id'), 'email_ab_tests', ['id'], unique=False)
    op.create_index('idx_ab_test_status', 'email_ab_tests', ['status'], unique=False)
    op.create_index('idx_ab_test_dates', 'email_ab_tests', ['start_date', 'end_date'], unique=False)
    
    # EMAIL_AB_VARIANTS
    op.create_table(
        'email_ab_variants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('ab_test_id', sa.String(), nullable=False),
        sa.Column('variant_name', sa.String(length=10), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=False),
        sa.Column('subject_template', sa.String(length=500), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('sent_count', sa.Integer(), nullable=False),
        sa.Column('delivered_count', sa.Integer(), nullable=False),
        sa.Column('opened_count', sa.Integer(), nullable=False),
        sa.Column('clicked_count', sa.Integer(), nullable=False),
        sa.Column('bounced_count', sa.Integer(), nullable=False),
        sa.Column('delivery_rate', sa.Float(), nullable=True),
        sa.Column('open_rate', sa.Float(), nullable=True),
        sa.Column('click_rate', sa.Float(), nullable=True),
        sa.Column('ctr', sa.Float(), nullable=True),
        sa.Column('is_winner', sa.String(), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ab_test_id'], ['email_ab_tests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_ab_variants_id'), 'email_ab_variants', ['id'], unique=False)
    op.create_index(op.f('ix_email_ab_variants_ab_test_id'), 'email_ab_variants', ['ab_test_id'], unique=False)
    op.create_index('idx_ab_variant_test', 'email_ab_variants', ['ab_test_id', 'variant_name'], unique=False)
    
    # EMAIL_TRACKING
    op.create_table(
        'email_tracking',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('open_count', sa.Integer(), nullable=False),
        sa.Column('first_click_at', sa.DateTime(), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=False),
        sa.Column('bounced', sa.Boolean(), nullable=False),
        sa.Column('bounce_type', sa.String(length=20), nullable=True),
        sa.Column('bounce_reason', sa.String(length=500), nullable=True),
        sa.Column('spam_complaint', sa.Boolean(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('email_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Basic indexes
    op.create_index(op.f('ix_email_tracking_id'), 'email_tracking', ['id'], unique=False)
    op.create_index(op.f('ix_email_tracking_message_id'), 'email_tracking', ['message_id'], unique=True)
    op.create_index(op.f('ix_email_tracking_user_id'), 'email_tracking', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_tracking_email'), 'email_tracking', ['email'], unique=False)
    op.create_index(op.f('ix_email_tracking_template_name'), 'email_tracking', ['template_name'], unique=False)
    op.create_index(op.f('ix_email_tracking_sent_at'), 'email_tracking', ['sent_at'], unique=False)
    # Composite indexes
    op.create_index('idx_email_tracking_user_sent', 'email_tracking', ['user_id', 'sent_at'], unique=False)
    op.create_index('idx_email_tracking_email_sent', 'email_tracking', ['email', 'sent_at'], unique=False)
    op.create_index('idx_email_tracking_template_sent', 'email_tracking', ['template_name', 'sent_at'], unique=False)
    
    # EMAIL_CLICKS
    op.create_table(
        'email_clicks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tracking_id', sa.String(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['tracking_id'], ['email_tracking.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_clicks_id'), 'email_clicks', ['id'], unique=False)
    op.create_index(op.f('ix_email_clicks_tracking_id'), 'email_clicks', ['tracking_id'], unique=False)
    op.create_index(op.f('ix_email_clicks_clicked_at'), 'email_clicks', ['clicked_at'], unique=False)
    
    # EMAIL_SUBSCRIPTIONS
    op.create_table(
        'email_subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False),
        sa.Column('notification_emails', sa.Boolean(), nullable=False),
        sa.Column('product_updates', sa.Boolean(), nullable=False),
        sa.Column('newsletter', sa.Boolean(), nullable=False),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_reason', sa.String(length=500), nullable=True),
        sa.Column('unsubscribe_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_subscriptions_id'), 'email_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_email_subscriptions_email'), 'email_subscriptions', ['email'], unique=True)
    op.create_index(op.f('ix_email_subscriptions_user_id'), 'email_subscriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_subscriptions_unsubscribe_token'), 'email_subscriptions', ['unsubscribe_token'], unique=True)
    
    # ========================================================================
    # FILE UPLOAD TABLES
    # ========================================================================
    
    # FILES
    op.create_table(
        'files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('storage_provider', sa.String(length=50), nullable=False),
        sa.Column('public_url', sa.String(length=1000), nullable=True),
        sa.Column('cdn_url', sa.String(length=1000), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('file_metadata', sa.JSON(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    op.create_index(op.f('ix_files_user_id'), 'files', ['user_id'], unique=False)
    op.create_index(op.f('ix_files_client_id'), 'files', ['client_id'], unique=False)
    op.create_index(op.f('ix_files_mime_type'), 'files', ['mime_type'], unique=False)
    op.create_index(op.f('ix_files_checksum'), 'files', ['checksum'], unique=False)
    
    # FILE_SHARES
    op.create_table(
        'file_shares',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('shared_by', sa.String(), nullable=False),
        sa.Column('shared_with', sa.String(), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ),
        sa.ForeignKeyConstraint(['shared_by'], ['app_user.id'], ),
        sa.ForeignKeyConstraint(['shared_with'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_shares_file_id'), 'file_shares', ['file_id'], unique=False)
    op.create_index(op.f('ix_file_shares_shared_with'), 'file_shares', ['shared_with'], unique=False)
    
    # MULTIPART_UPLOADS (Chunked upload tracking)
    op.create_table(
        'multipart_uploads',
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('total_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('upload_id')
    )
    op.create_index(op.f('ix_multipart_uploads_file_id'), 'multipart_uploads', ['file_id'], unique=False)
    
    # PENDING_UPLOADS
    op.create_table(
        'pending_uploads',
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('upload_id')
    )
    
    # UPLOAD_PARTS (Individual parts of chunked uploads)
    op.create_table(
        'upload_parts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('part_number', sa.Integer(), nullable=False),
        sa.Column('etag', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['upload_id'], ['multipart_uploads.upload_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_upload_parts_upload_id'), 'upload_parts', ['upload_id'], unique=False)
    
    # ========================================================================
    # ASYNC TASKS TABLE (202 Accepted Pattern)
    # ========================================================================
    
    # ASYNC_TASKS (from 20251103)
    op.create_table(
        'async_tasks',
        sa.Column('id', sa.String(length=36), nullable=False, comment='Unique task ID (UUID)'),
        sa.Column('task_type', sa.String(length=100), nullable=False, comment='Task type identifier'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='Task status'),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Input data (JSON)'),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Result data (JSON)'),
        sa.Column('error', sa.Text(), nullable=True, comment='Error message if failed'),
        sa.Column('progress_percentage', sa.Integer(), nullable=True, comment='Progress 0-100'),
        sa.Column('progress_message', sa.String(length=500), nullable=True, comment='Progress description'),
        sa.Column('client_id', sa.String(length=36), nullable=False, comment='Tenant ID'),
        sa.Column('created_by', sa.String(length=36), nullable=False, comment='User who created task'),
        sa.Column('celery_task_id', sa.String(length=100), nullable=True, comment='Celery task ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='When processing started'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='When task finished'),
        sa.PrimaryKeyConstraint('id'),
        comment='Async tasks for long-running operations (202 Accepted pattern)'
    )
    # Basic indexes
    op.create_index('ix_async_tasks_id', 'async_tasks', ['id'])
    op.create_index('ix_async_tasks_task_type', 'async_tasks', ['task_type'])
    op.create_index('ix_async_tasks_status', 'async_tasks', ['status'])
    op.create_index('ix_async_tasks_client_id', 'async_tasks', ['client_id'])
    op.create_index('ix_async_tasks_created_by', 'async_tasks', ['created_by'])
    op.create_index('ix_async_tasks_celery_task_id', 'async_tasks', ['celery_task_id'])
    # Composite indexes
    op.create_index('ix_async_tasks_client_created_by', 'async_tasks', ['client_id', 'created_by'])
    op.create_index('ix_async_tasks_status_created_at', 'async_tasks', ['status', 'created_at'])
    op.create_index('ix_async_tasks_task_type_status', 'async_tasks', ['task_type', 'status'])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    
    # Drop async_tasks
    op.drop_index('ix_async_tasks_task_type_status', table_name='async_tasks')
    op.drop_index('ix_async_tasks_status_created_at', table_name='async_tasks')
    op.drop_index('ix_async_tasks_client_created_by', table_name='async_tasks')
    op.drop_index('ix_async_tasks_celery_task_id', table_name='async_tasks')
    op.drop_index('ix_async_tasks_created_by', table_name='async_tasks')
    op.drop_index('ix_async_tasks_client_id', table_name='async_tasks')
    op.drop_index('ix_async_tasks_status', table_name='async_tasks')
    op.drop_index('ix_async_tasks_task_type', table_name='async_tasks')
    op.drop_index('ix_async_tasks_id', table_name='async_tasks')
    op.drop_table('async_tasks')
    
    # Drop file tables (child tables first)
    op.drop_index(op.f('ix_upload_parts_upload_id'), table_name='upload_parts')
    op.drop_table('upload_parts')
    op.drop_index(op.f('ix_file_shares_shared_with'), table_name='file_shares')
    op.drop_index(op.f('ix_file_shares_file_id'), table_name='file_shares')
    op.drop_table('file_shares')
    op.drop_table('pending_uploads')
    op.drop_index(op.f('ix_multipart_uploads_file_id'), table_name='multipart_uploads')
    op.drop_table('multipart_uploads')
    op.drop_index(op.f('ix_files_checksum'), table_name='files')
    op.drop_index(op.f('ix_files_mime_type'), table_name='files')
    op.drop_index(op.f('ix_files_client_id'), table_name='files')
    op.drop_index(op.f('ix_files_user_id'), table_name='files')
    op.drop_index(op.f('ix_files_id'), table_name='files')
    op.drop_table('files')
    
    # Drop email tables
    op.drop_index(op.f('ix_email_clicks_clicked_at'), table_name='email_clicks')
    op.drop_index(op.f('ix_email_clicks_tracking_id'), table_name='email_clicks')
    op.drop_index(op.f('ix_email_clicks_id'), table_name='email_clicks')
    op.drop_table('email_clicks')
    op.drop_index('idx_email_tracking_template_sent', table_name='email_tracking')
    op.drop_index('idx_email_tracking_email_sent', table_name='email_tracking')
    op.drop_index('idx_email_tracking_user_sent', table_name='email_tracking')
    op.drop_index(op.f('ix_email_tracking_sent_at'), table_name='email_tracking')
    op.drop_index(op.f('ix_email_tracking_template_name'), table_name='email_tracking')
    op.drop_index(op.f('ix_email_tracking_email'), table_name='email_tracking')
    op.drop_index(op.f('ix_email_tracking_user_id'), table_name='email_tracking')
    op.drop_index(op.f('ix_email_tracking_message_id'), table_name='email_tracking')
    op.drop_index(op.f('ix_email_tracking_id'), table_name='email_tracking')
    op.drop_table('email_tracking')
    op.drop_index(op.f('ix_email_subscriptions_unsubscribe_token'), table_name='email_subscriptions')
    op.drop_index(op.f('ix_email_subscriptions_user_id'), table_name='email_subscriptions')
    op.drop_index(op.f('ix_email_subscriptions_email'), table_name='email_subscriptions')
    op.drop_index(op.f('ix_email_subscriptions_id'), table_name='email_subscriptions')
    op.drop_table('email_subscriptions')
    op.drop_index('idx_ab_variant_test', table_name='email_ab_variants')
    op.drop_index(op.f('ix_email_ab_variants_ab_test_id'), table_name='email_ab_variants')
    op.drop_index(op.f('ix_email_ab_variants_id'), table_name='email_ab_variants')
    op.drop_table('email_ab_variants')
    op.drop_index('idx_ab_test_dates', table_name='email_ab_tests')
    op.drop_index('idx_ab_test_status', table_name='email_ab_tests')
    op.drop_index(op.f('ix_email_ab_tests_id'), table_name='email_ab_tests')
    op.drop_table('email_ab_tests')
    
    # Drop auth & security tables
    op.drop_index(op.f('ix_webauthn_credential_revoked_at'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_client_id'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_user_id'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_credential_id'), table_name='webauthn_credential')
    op.drop_index(op.f('ix_webauthn_credential_id'), table_name='webauthn_credential')
    op.drop_table('webauthn_credential')
    op.drop_index('idx_session_expires_revoked', table_name='user_session')
    op.drop_index('idx_session_client_active', table_name='user_session')
    op.drop_index('idx_session_user_activity', table_name='user_session')
    op.drop_index('idx_session_user_active', table_name='user_session')
    op.drop_index('idx_session_client_user', table_name='user_session')
    op.drop_index(op.f('ix_user_session_revoked_at'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_expires_at'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_client_id'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_user_id'), table_name='user_session')
    op.drop_index(op.f('ix_user_session_id'), table_name='user_session')
    op.drop_table('user_session')
    op.drop_index(op.f('ix_backup_code_used'), table_name='backup_code')
    op.drop_index(op.f('ix_backup_code_client_id'), table_name='backup_code')
    op.drop_index(op.f('ix_backup_code_user_id'), table_name='backup_code')
    op.drop_index(op.f('ix_backup_code_id'), table_name='backup_code')
    op.drop_table('backup_code')
    op.drop_index(op.f('ix_api_key_revoked_at'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_expires_at'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_client_id'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_user_id'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_id'), table_name='api_key')
    op.drop_table('api_key')
    
    # Drop audit table
    op.drop_index('idx_audit_status', table_name='audit_log')
    # op.drop_index('idx_audit_user_success_date', table_name='audit_log')
    # op.drop_index('idx_audit_client_category_date', table_name='audit_log')
    op.drop_index('idx_audit_user_event', table_name='audit_log')
    op.drop_index('idx_audit_user_created', table_name='audit_log')
    op.drop_index('idx_audit_client_event', table_name='audit_log')
    op.drop_index('idx_audit_client_created', table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_created_at'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_event_type'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_client_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_user_id'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_id'), table_name='audit_log')
    op.drop_table('audit_log')
    
    # Drop core tables (child first, then parent)
    op.drop_index(op.f('ix_permission_user_id'), table_name='permission')
    op.drop_index(op.f('ix_permission_client_id'), table_name='permission')
    op.drop_table('permission')
    
    # Drop app_user (many indexes)
    op.drop_index('idx_app_user_client_username', table_name='app_user')
    op.drop_index('idx_app_user_client_email_unique', table_name='app_user')
    op.drop_index('idx_app_user_email_verified', table_name='app_user')
    op.drop_index('idx_app_user_client_role', table_name='app_user')
    op.drop_index('idx_app_user_client_active', table_name='app_user')
    op.drop_index('idx_user_email_active', table_name='app_user')
    op.drop_index('idx_user_client_username', table_name='app_user')
    op.drop_index('idx_user_client_created', table_name='app_user')
    op.drop_index('idx_user_client_active', table_name='app_user')
    op.drop_index(op.f('ix_app_user_role'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_is_active'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_client_id'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_email'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_username'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_id'), table_name='app_user')
    op.drop_table('app_user')
    
    # Drop client (root table)
    op.drop_index(op.f('ix_client_active'), table_name='client')
    op.drop_index(op.f('ix_client_api_key'), table_name='client')
    op.drop_index(op.f('ix_client_subdomain'), table_name='client')
    op.drop_index(op.f('ix_client_name'), table_name='client')
    op.drop_index(op.f('ix_client_id'), table_name='client')
    op.drop_table('client')

