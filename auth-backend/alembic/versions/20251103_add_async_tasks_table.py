"""add async tasks table

Revision ID: 20251103_async_tasks
Revises: 20251102_add_performance_indexes
Create Date: 2025-11-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251103_async_tasks'
down_revision = '20251102_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create async_tasks table for 202 Accepted pattern."""
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
    
    # Indexes for performance
    op.create_index('ix_async_tasks_id', 'async_tasks', ['id'])
    op.create_index('ix_async_tasks_task_type', 'async_tasks', ['task_type'])
    op.create_index('ix_async_tasks_status', 'async_tasks', ['status'])
    op.create_index('ix_async_tasks_client_id', 'async_tasks', ['client_id'])
    op.create_index('ix_async_tasks_created_by', 'async_tasks', ['created_by'])
    op.create_index('ix_async_tasks_celery_task_id', 'async_tasks', ['celery_task_id'])
    
    # Composite indexes for common queries
    op.create_index(
        'ix_async_tasks_client_created_by',
        'async_tasks',
        ['client_id', 'created_by']
    )
    op.create_index(
        'ix_async_tasks_status_created_at',
        'async_tasks',
        ['status', 'created_at']
    )
    op.create_index(
        'ix_async_tasks_task_type_status',
        'async_tasks',
        ['task_type', 'status']
    )


def downgrade() -> None:
    """Drop async_tasks table."""
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

