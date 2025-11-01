"""add user kyc fields

Revision ID: 20251101_1930
Revises: 20251101_1852
Create Date: 2025-11-01 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251101_1930'
down_revision = '20251101_1852'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add KYC fields to app_user table."""
    op.add_column('app_user', sa.Column('kyc_document_id', sa.String(255), nullable=True))
    op.add_column('app_user', sa.Column('kyc_status', sa.String(50), nullable=True))
    op.add_column('app_user', sa.Column('kyc_verified_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove KYC fields from app_user table."""
    op.drop_column('app_user', 'kyc_verified_at')
    op.drop_column('app_user', 'kyc_status')
    op.drop_column('app_user', 'kyc_document_id')

