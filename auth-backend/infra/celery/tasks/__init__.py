"""Celery tasks package"""
from .email_tasks import (
    send_email_task,
    send_template_email_task,
    send_bulk_email_task,
    send_scheduled_email_task,
)

__all__ = [
    "send_email_task",
    "send_template_email_task",
    "send_bulk_email_task",
    "send_scheduled_email_task",
]

