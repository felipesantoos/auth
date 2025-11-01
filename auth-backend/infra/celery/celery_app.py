"""
Celery Application Configuration
Background task processing for async operations
"""
import logging
from celery import Celery
from config.settings import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "auth_system",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        'infra.celery.tasks.email_tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    
    # Results
    result_expires=3600,  # 1 hour
    
    # Rate limiting
    task_annotations={
        'infra.celery.tasks.email_tasks.send_email_task': {
            'rate_limit': '100/m'  # 100 emails per minute
        },
        'infra.celery.tasks.email_tasks.send_bulk_email_task': {
            'rate_limit': '10/m'  # 10 bulk operations per minute
        }
    },
    
    # Retry policy
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)

logger.info(f"Celery app initialized with broker: {settings.celery_broker_url}")


# Periodic tasks (optional - for scheduled emails)
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks (if needed)."""
    # Example: Clean up old tracking data every day
    # sender.add_periodic_task(
    #     86400.0,  # Every 24 hours
    #     cleanup_old_tracking_data.s(),
    #     name='cleanup-tracking-data'
    # )
    pass

