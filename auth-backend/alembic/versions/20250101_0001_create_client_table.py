"""create_client_table

Revision ID: 20250101_0001
Revises: 
Create Date: 2025-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250101_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration"""
    op.create_table(
        'client',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('subdomain', sa.String(length=100), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_client_id'), 'client', ['id'], unique=False)
    op.create_index(op.f('ix_client_name'), 'client', ['name'], unique=False)
    op.create_index(op.f('ix_client_subdomain'), 'client', ['subdomain'], unique=True)
    op.create_index(op.f('ix_client_api_key'), 'client', ['api_key'], unique=True)
    op.create_index(op.f('ix_client_active'), 'client', ['active'], unique=False)


def downgrade() -> None:
    """Revert migration"""
    op.drop_index(op.f('ix_client_active'), table_name='client')
    op.drop_index(op.f('ix_client_api_key'), table_name='client')
    op.drop_index(op.f('ix_client_subdomain'), table_name='client')
    op.drop_index(op.f('ix_client_name'), table_name='client')
    op.drop_index(op.f('ix_client_id'), table_name='client')
    op.drop_table('client')

