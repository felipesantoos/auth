"""create_app_user_table

Revision ID: 20250101_0002
Revises: 20250101_0001
Create Date: 2025-01-01 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250101_0002'
down_revision: Union[str, None] = '20250101_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration"""
    op.create_table(
        'app_user',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_app_user_id'), 'app_user', ['id'], unique=False)
    op.create_index(op.f('ix_app_user_username'), 'app_user', ['username'], unique=False)
    op.create_index(op.f('ix_app_user_email'), 'app_user', ['email'], unique=False)
    op.create_index(op.f('ix_app_user_role'), 'app_user', ['role'], unique=False)
    op.create_index(op.f('ix_app_user_is_active'), 'app_user', ['is_active'], unique=False)
    op.create_index(op.f('ix_app_user_client_id'), 'app_user', ['client_id'], unique=False)
    
    # Create unique constraint for email+client_id (multi-tenant: email unique per client)
    op.create_index('ix_app_user_email_client_id', 'app_user', ['email', 'client_id'], unique=True)


def downgrade() -> None:
    """Revert migration"""
    op.drop_index('ix_app_user_email_client_id', table_name='app_user')
    op.drop_index(op.f('ix_app_user_client_id'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_is_active'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_role'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_email'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_username'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_id'), table_name='app_user')
    op.drop_table('app_user')

