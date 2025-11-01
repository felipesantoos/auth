"""add file upload tables

Revision ID: 20251101_1848
Revises: previous_migration
Create Date: 2025-11-01 18:48:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251101_1848'
down_revision: Union[str, None] = None  # Will be set to latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create file upload related tables."""
    
    # Files table
    op.create_table(
        'files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('stored_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('storage_provider', sa.String(50), nullable=False),
        sa.Column('public_url', sa.String(1000), nullable=True),
        sa.Column('cdn_url', sa.String(1000), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE')
    )
    
    # Indexes
    op.create_index('ix_files_id', 'files', ['id'])
    op.create_index('ix_files_user_id', 'files', ['user_id'])
    op.create_index('ix_files_client_id', 'files', ['client_id'])
    op.create_index('ix_files_mime_type', 'files', ['mime_type'])
    op.create_index('ix_files_checksum', 'files', ['checksum'])
    
    # Pending uploads table
    op.create_table(
        'pending_uploads',
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('upload_id'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE')
    )
    
    # File shares table
    op.create_table(
        'file_shares',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('shared_by', sa.String(), nullable=False),
        sa.Column('shared_with', sa.String(), nullable=False),
        sa.Column('permission', sa.String(20), nullable=False, server_default='read'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by'], ['app_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_with'], ['app_user.id'], ondelete='CASCADE')
    )
    
    # Indexes
    op.create_index('ix_file_shares_file_id', 'file_shares', ['file_id'])
    op.create_index('ix_file_shares_shared_with', 'file_shares', ['shared_with'])


def downgrade() -> None:
    """Drop file upload related tables."""
    op.drop_index('ix_file_shares_shared_with', table_name='file_shares')
    op.drop_index('ix_file_shares_file_id', table_name='file_shares')
    op.drop_table('file_shares')
    op.drop_table('pending_uploads')
    op.drop_index('ix_files_checksum', table_name='files')
    op.drop_index('ix_files_mime_type', table_name='files')
    op.drop_index('ix_files_client_id', table_name='files')
    op.drop_index('ix_files_user_id', table_name='files')
    op.drop_index('ix_files_id', table_name='files')
    op.drop_table('files')

