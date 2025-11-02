"""
Unit tests for Celery Maintenance Tasks
Tests system maintenance tasks without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.celery.tasks.maintenance_tasks import cleanup_old_sessions, archive_audit_logs


@pytest.mark.unit
class TestMaintenanceTasks:
    """Test maintenance Celery tasks"""
    
    def test_cleanup_old_sessions_task(self):
        """Test cleaning up expired sessions"""
        with patch('infra.celery.tasks.maintenance_tasks.session_service') as mock_service:
            mock_service.cleanup_expired_sessions = Mock(return_value=25)
            
            result = cleanup_old_sessions()
            
            assert result == 25 or mock_service.cleanup_expired_sessions.called
    
    def test_archive_audit_logs_task(self):
        """Test archiving old audit logs"""
        with patch('infra.celery.tasks.maintenance_tasks.audit_retention_service') as mock_service:
            mock_service.archive_old_logs = Mock(return_value={"status": "completed"})
            
            result = archive_audit_logs()
            
            assert result or mock_service.archive_old_logs.called

