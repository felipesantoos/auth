"""add email ab testing tables

Revision ID: add_email_ab_testing
Revises: add_email_tracking
Create Date: 2025-11-01 18:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_email_ab_testing'
down_revision: Union[str, None] = 'add_email_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create A/B testing tables."""
    
    # Create email_ab_tests table
    op.create_table(
        'email_ab_tests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('distribution_type', sa.String(length=20), nullable=False, server_default='equal'),
        sa.Column('variant_count', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('winner_variant', sa.String(length=10), nullable=True),
        sa.Column('winner_metric', sa.String(length=20), nullable=True),
        sa.Column('auto_select_winner', sa.String(), nullable=False, server_default='false'),
        sa.Column('min_sample_size', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('confidence_level', sa.Integer(), nullable=False, server_default='95'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('winner_selected_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for email_ab_tests
    op.create_index('idx_ab_test_dates', 'email_ab_tests', ['start_date', 'end_date'])
    op.create_index('idx_ab_test_status', 'email_ab_tests', ['status'])
    op.create_index('ix_email_ab_tests_id', 'email_ab_tests', ['id'])
    
    # Create email_ab_variants table
    op.create_table(
        'email_ab_variants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('ab_test_id', sa.String(), nullable=False),
        sa.Column('variant_name', sa.String(length=10), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=False),
        sa.Column('subject_template', sa.String(length=500), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('sent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delivered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('opened_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicked_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bounced_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delivery_rate', sa.Float(), nullable=True),
        sa.Column('open_rate', sa.Float(), nullable=True),
        sa.Column('click_rate', sa.Float(), nullable=True),
        sa.Column('ctr', sa.Float(), nullable=True),
        sa.Column('is_winner', sa.String(), nullable=False, server_default='false'),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ab_test_id'], ['email_ab_tests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for email_ab_variants
    op.create_index('idx_ab_variant_test', 'email_ab_variants', ['ab_test_id', 'variant_name'])
    op.create_index('idx_ab_variant_test_id', 'email_ab_variants', ['ab_test_id'])
    op.create_index('ix_email_ab_variants_id', 'email_ab_variants', ['id'])


def downgrade() -> None:
    """Drop A/B testing tables."""
    
    # Drop email_ab_variants
    op.drop_index('ix_email_ab_variants_id', table_name='email_ab_variants')
    op.drop_index('idx_ab_variant_test_id', table_name='email_ab_variants')
    op.drop_index('idx_ab_variant_test', table_name='email_ab_variants')
    op.drop_table('email_ab_variants')
    
    # Drop email_ab_tests
    op.drop_index('ix_email_ab_tests_id', table_name='email_ab_tests')
    op.drop_index('idx_ab_test_status', table_name='email_ab_tests')
    op.drop_index('idx_ab_test_dates', table_name='email_ab_tests')
    op.drop_table('email_ab_tests')

