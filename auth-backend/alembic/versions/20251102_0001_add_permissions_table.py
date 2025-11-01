"""add permissions table

Revision ID: abc123456789
Revises: 625f6b9fbb95
Create Date: 2025-11-02 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc123456789'
down_revision = '625f6b9fbb95'
branch_labels = None
depends_on = None


def upgrade():
    """Add permissions table for fine-grained access control"""
    op.create_table(
        'permission',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),  # String livre!
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('granted_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_permission_user_id', 'permission', ['user_id'])
    op.create_index('ix_permission_client_id', 'permission', ['client_id'])
    op.create_index('ix_permission_resource_type', 'permission', ['resource_type'])


def downgrade():
    """Remove permissions table"""
    op.drop_index('ix_permission_resource_type', table_name='permission')
    op.drop_index('ix_permission_client_id', table_name='permission')
    op.drop_index('ix_permission_user_id', table_name='permission')
    op.drop_table('permission')

