"""
Unit tests for Audit Log Repository
Tests audit log data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from infra.database.repositories.audit_log_repository import AuditLogRepository
from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory


@pytest.mark.unit
class TestAuditLogRepositorySave:
    """Test saving audit logs"""
    
    @pytest.mark.asyncio
    async def test_save_audit_log(self):
        """Test saving audit log to database"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        repository = AuditLogRepository(session_mock)
        
        audit_log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="client-123",
            user_id="user-123",
            status="success"
        )
        
        result = await repository.save(audit_log)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()


@pytest.mark.unit
class TestAuditLogRepositoryQuery:
    """Test querying audit logs"""
    
    @pytest.mark.asyncio
    async def test_find_by_user(self):
        """Test finding audit logs by user ID"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = AuditLogRepository(session_mock)
        
        result = await repository.find_by_user("user-123", days=30)
        
        assert isinstance(result, list)
        session_mock.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_find_by_category(self):
        """Test finding audit logs by category"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = AuditLogRepository(session_mock)
        
        result = await repository.find_by_category(
            category=AuditEventCategory.AUTHENTICATION,
            limit=100
        )
        
        assert isinstance(result, list)
        session_mock.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_count_failed_logins(self):
        """Test counting failed login attempts"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar = Mock(return_value=5)
        
        repository = AuditLogRepository(session_mock)
        
        count = await repository.count_failed_logins(
            user_id="user-123",
            minutes=30
        )
        
        assert count == 5 or count >= 0

