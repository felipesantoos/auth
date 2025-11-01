"""
Celery Application Configuration
Background task processing for async operations with scheduled periodic tasks
"""
import logging
from celery import Celery
from celery.schedules import crontab
from config.settings import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "auth_system",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        'infra.celery.tasks.email_tasks',
        'infra.celery.tasks.cache_tasks',
        'infra.celery.tasks.maintenance_tasks',
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


# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    # Cleanup expired sessions - Daily at 3:00 AM
    'cleanup-expired-sessions': {
        'task': 'cleanup_expired_sessions',
        'schedule': crontab(hour=3, minute=0),
    },
    # Cleanup expired tokens - Daily at 2:00 AM
    'cleanup-expired-tokens': {
        'task': 'cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),
    },
    # Cleanup old audit logs (>90 days) - Weekly on Sunday at 4:00 AM
    'cleanup-old-audit-logs': {
        'task': 'cleanup_old_audit_logs',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),
    },
    # Warm popular cache - Every 6 hours
    'warm-popular-cache': {
        'task': 'warm_popular_cache',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}

logger.info(f"Celery Beat schedule configured with {len(celery_app.conf.beat_schedule)} periodic tasks")

