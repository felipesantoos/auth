"""add email tracking tables

Revision ID: add_email_tracking
Revises: 625f6b9fbb95
Create Date: 2025-11-01 17:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_email_tracking'
down_revision: Union[str, None] = '625f6b9fbb95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create email tracking, clicks, and subscriptions tables."""
    
    # Create email_tracking table
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
        sa.Column('open_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('first_click_at', sa.DateTime(), nullable=True),
        sa.Column('click_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bounced', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('bounce_type', sa.String(length=20), nullable=True),
        sa.Column('bounce_reason', sa.String(length=500), nullable=True),
        sa.Column('spam_complaint', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for email_tracking
    op.create_index('idx_email_tracking_email', 'email_tracking', ['email'])
    op.create_index('idx_email_tracking_email_sent', 'email_tracking', ['email', 'sent_at'])
    op.create_index('idx_email_tracking_message_id', 'email_tracking', ['message_id'], unique=True)
    op.create_index('idx_email_tracking_sent_at', 'email_tracking', ['sent_at'])
    op.create_index('idx_email_tracking_template_name', 'email_tracking', ['template_name'])
    op.create_index('idx_email_tracking_template_sent', 'email_tracking', ['template_name', 'sent_at'])
    op.create_index('idx_email_tracking_user_id', 'email_tracking', ['user_id'])
    op.create_index('idx_email_tracking_user_sent', 'email_tracking', ['user_id', 'sent_at'])
    op.create_index('ix_email_tracking_id', 'email_tracking', ['id'])
    
    # Create email_clicks table
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
    
    # Indexes for email_clicks
    op.create_index('idx_email_clicks_clicked_at', 'email_clicks', ['clicked_at'])
    op.create_index('idx_email_clicks_tracking_id', 'email_clicks', ['tracking_id'])
    op.create_index('ix_email_clicks_id', 'email_clicks', ['id'])
    
    # Create email_subscriptions table
    op.create_table(
        'email_subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notification_emails', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('product_updates', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('newsletter', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_reason', sa.String(length=500), nullable=True),
        sa.Column('unsubscribe_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for email_subscriptions
    op.create_index('idx_email_subscriptions_email', 'email_subscriptions', ['email'], unique=True)
    op.create_index('idx_email_subscriptions_unsubscribe_token', 'email_subscriptions', ['unsubscribe_token'], unique=True)
    op.create_index('idx_email_subscriptions_user_id', 'email_subscriptions', ['user_id'])
    op.create_index('ix_email_subscriptions_id', 'email_subscriptions', ['id'])


def downgrade() -> None:
    """Drop email tracking, clicks, and subscriptions tables."""
    
    # Drop email_subscriptions
    op.drop_index('ix_email_subscriptions_id', table_name='email_subscriptions')
    op.drop_index('idx_email_subscriptions_user_id', table_name='email_subscriptions')
    op.drop_index('idx_email_subscriptions_unsubscribe_token', table_name='email_subscriptions')
    op.drop_index('idx_email_subscriptions_email', table_name='email_subscriptions')
    op.drop_table('email_subscriptions')
    
    # Drop email_clicks
    op.drop_index('ix_email_clicks_id', table_name='email_clicks')
    op.drop_index('idx_email_clicks_tracking_id', table_name='email_clicks')
    op.drop_index('idx_email_clicks_clicked_at', table_name='email_clicks')
    op.drop_table('email_clicks')
    
    # Drop email_tracking
    op.drop_index('ix_email_tracking_id', table_name='email_tracking')
    op.drop_index('idx_email_tracking_user_sent', table_name='email_tracking')
    op.drop_index('idx_email_tracking_user_id', table_name='email_tracking')
    op.drop_index('idx_email_tracking_template_sent', table_name='email_tracking')
    op.drop_index('idx_email_tracking_template_name', table_name='email_tracking')
    op.drop_index('idx_email_tracking_sent_at', table_name='email_tracking')
    op.drop_index('idx_email_tracking_message_id', table_name='email_tracking')
    op.drop_index('idx_email_tracking_email_sent', table_name='email_tracking')
    op.drop_index('idx_email_tracking_email', table_name='email_tracking')
    op.drop_table('email_tracking')

