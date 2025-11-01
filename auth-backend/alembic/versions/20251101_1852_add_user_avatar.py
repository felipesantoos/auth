"""add user avatar

Revision ID: 20251101_1852
Revises: 20251101_1848
Create Date: 2025-11-01 18:52:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251101_1852'
down_revision: Union[str, None] = '20251101_1848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add avatar_url column to app_user table."""
    op.add_column('app_user', sa.Column('avatar_url', sa.String(1000), nullable=True))


def downgrade() -> None:
    """Remove avatar_url column from app_user table."""
    op.drop_column('app_user', 'avatar_url')

