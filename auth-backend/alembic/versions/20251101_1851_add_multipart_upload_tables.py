"""add multipart upload tables

Revision ID: 20251101_1851
Revises: 20251101_1848
Create Date: 2025-11-01 18:51:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251101_1851'
down_revision: Union[str, None] = '20251101_1848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create multipart upload tables."""
    
    # Multipart uploads table
    op.create_table(
        'multipart_uploads',
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('s3_key', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='initiated'),
        sa.Column('total_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_size', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('upload_id'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_multipart_uploads_file_id', 'multipart_uploads', ['file_id'])
    
    # Upload parts table
    op.create_table(
        'upload_parts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('part_number', sa.Integer(), nullable=False),
        sa.Column('etag', sa.String(100), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['upload_id'], ['multipart_uploads.upload_id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_upload_parts_upload_id', 'upload_parts', ['upload_id'])


def downgrade() -> None:
    """Drop multipart upload tables."""
    op.drop_index('ix_upload_parts_upload_id', table_name='upload_parts')
    op.drop_table('upload_parts')
    op.drop_index('ix_multipart_uploads_file_id', table_name='multipart_uploads')
    op.drop_table('multipart_uploads')

