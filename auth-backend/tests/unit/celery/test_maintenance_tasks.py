"""
Unit tests for Celery Maintenance Tasks
Tests system maintenance tasks without external dependencies
"""
import pytest
from infra.celery.tasks.maintenance_tasks import (
    cleanup_expired_sessions_task,
    cleanup_expired_tokens_task,
    cleanup_old_audit_logs_task,
    cleanup_expired_api_keys_task
)


@pytest.mark.unit
class TestMaintenanceTasks:
    """Test maintenance Celery tasks"""
    
    def test_cleanup_expired_sessions_task_exists(self):
        """Test cleanup expired sessions task exists"""
        assert callable(cleanup_expired_sessions_task)
    
    def test_cleanup_expired_tokens_task_exists(self):
        """Test cleanup expired tokens task exists"""
        assert callable(cleanup_expired_tokens_task)
    
    def test_cleanup_old_audit_logs_task_exists(self):
        """Test cleanup old audit logs task exists"""
        assert callable(cleanup_old_audit_logs_task)
    
    def test_cleanup_expired_api_keys_task_exists(self):
        """Test cleanup expired API keys task exists"""
        assert callable(cleanup_expired_api_keys_task)
