"""
Unit tests for Audit Service
Tests audit logging logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from core.services.audit.audit_service import AuditService
from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory
from core.domain.audit.entity_change import EntityChange


@pytest.mark.unit
class TestLogEvent:
    """Test general event logging"""
    
    @pytest.mark.asyncio
    async def test_log_event_creates_audit_log(self):
        """Test log_event creates and saves audit log"""
        repository_mock = AsyncMock()
        repository_mock.save = AsyncMock(return_value=Mock(id="log-123"))
        
        service = AuditService(repository_mock)
        
        log = await service.log_event(
            client_id="client-123",
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id="user-123",
            username="john_doe"
        )
        
        assert repository_mock.save.called
        assert log is not None
    
    @pytest.mark.asyncio
    async def test_log_event_sets_default_action(self):
        """Test log_event sets default action from event_type"""
        repository_mock = AsyncMock()
        saved_log = None
        
        async def capture_save(log):
            nonlocal saved_log
            saved_log = log
            return log
        
        repository_mock.save = AsyncMock(side_effect=capture_save)
        
        service = AuditService(repository_mock)
        
        await service.log_event(
            client_id="client-123",
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id="user-123"
        )
        
        assert saved_log is not None
        assert "Login Success" in saved_log.action
    
    @pytest.mark.asyncio
    async def test_log_event_handles_failure(self):
        """Test log_event handles save failures gracefully"""
        repository_mock = AsyncMock()
        repository_mock.save = AsyncMock(side_effect=Exception("DB error"))
        
        service = AuditService(repository_mock)
        
        # Should not raise exception
        log = await service.log_event(
            client_id="client-123",
            event_type=AuditEventType.LOGIN_SUCCESS
        )
        
        assert log is not None
        assert log.id is None  # Not saved


@pytest.mark.unit
class TestLogEntityChange:
    """Test entity change logging"""
    
    @pytest.mark.asyncio
    async def test_log_entity_change_records_changes(self):
        """Test log_entity_change records field-level changes"""
        repository_mock = AsyncMock()
        saved_log = None
        
        async def capture_save(log):
            nonlocal saved_log
            saved_log = log
            return log
        
        repository_mock.save = AsyncMock(side_effect=capture_save)
        
        service = AuditService(repository_mock)
        
        changes = [
            EntityChange(
                field="email",
                old_value="old@example.com",
                new_value="new@example.com",
                field_type="string",
                change_type="modified"
            )
        ]
        
        await service.log_entity_change(
            client_id="client-123",
            event_type=AuditEventType.ENTITY_UPDATED,
            entity_type="user",
            entity_id="user-123",
            entity_name="John Doe",
            changes=changes,
            user_id="admin-123"
        )
        
        assert saved_log is not None
        assert "user" in saved_log.resource_type
        assert "data_modification" in saved_log.tags
    
    @pytest.mark.asyncio
    async def test_log_entity_change_tags_deletion_as_critical(self):
        """Test entity deletion is tagged as critical"""
        repository_mock = AsyncMock()
        saved_log = None
        
        async def capture_save(log):
            nonlocal saved_log
            saved_log = log
            return log
        
        repository_mock.save = AsyncMock(side_effect=capture_save)
        
        service = AuditService(repository_mock)
        
        await service.log_entity_change(
            client_id="client-123",
            event_type=AuditEventType.ENTITY_DELETED,
            entity_type="project",
            entity_id="proj-123",
            entity_name="Important Project",
            changes=[],
            user_id="admin-123"
        )
        
        assert saved_log is not None
        assert "critical" in saved_log.tags


@pytest.mark.unit
class TestLogDataAccess:
    """Test data access logging"""
    
    @pytest.mark.asyncio
    async def test_log_data_access_tags_sensitive_data(self):
        """Test sensitive data access is properly tagged"""
        repository_mock = AsyncMock()
        saved_log = None
        
        async def capture_save(log):
            nonlocal saved_log
            saved_log = log
            return log
        
        repository_mock.save = AsyncMock(side_effect=capture_save)
        
        service = AuditService(repository_mock)
        
        await service.log_data_access(
            client_id="client-123",
            access_type="view",
            resource_type="medical_record",
            resource_id="record-123",
            resource_name="Patient Health Data",
            user_id="doctor-123",
            username="Dr. Smith",
            is_sensitive=True
        )
        
        assert saved_log is not None
        assert "sensitive" in saved_log.tags
        assert "pii" in saved_log.tags
        assert "compliance" in saved_log.tags
        assert saved_log.event_type == AuditEventType.SENSITIVE_DATA_ACCESSED
    
    @pytest.mark.asyncio
    async def test_log_data_access_handles_different_access_types(self):
        """Test different access types (view, download, export) are logged"""
        repository_mock = AsyncMock()
        service = AuditService(repository_mock)
        repository_mock.save = AsyncMock(return_value=Mock())
        
        # Test view
        await service.log_data_access(
            client_id="client-123",
            access_type="view",
            resource_type="document",
            resource_id="doc-123",
            resource_name="Report",
            user_id="user-123",
            username="john"
        )
        
        # Test download
        await service.log_data_access(
            client_id="client-123",
            access_type="download",
            resource_type="document",
            resource_id="doc-123",
            resource_name="Report",
            user_id="user-123",
            username="john"
        )
        
        assert repository_mock.save.call_count == 2


@pytest.mark.unit
class TestLogBusinessEvent:
    """Test business event logging"""
    
    @pytest.mark.asyncio
    async def test_log_business_event_tags_correctly(self):
        """Test business events are tagged correctly"""
        repository_mock = AsyncMock()
        saved_log = None
        
        async def capture_save(log):
            nonlocal saved_log
            saved_log = log
            return log
        
        repository_mock.save = AsyncMock(side_effect=capture_save)
        
        service = AuditService(repository_mock)
        
        await service.log_business_event(
            client_id="client-123",
            event_type=AuditEventType.WORKFLOW_COMPLETED,
            action="Completed approval workflow",
            user_id="user-123",
            username="john"
        )
        
        assert saved_log is not None
        assert "business_event" in saved_log.tags


@pytest.mark.unit
class TestLogAdminAction:
    """Test administrative action logging"""
    
    @pytest.mark.asyncio
    async def test_log_admin_action_tags_as_critical(self):
        """Test admin actions are tagged as critical"""
        repository_mock = AsyncMock()
        saved_log = None
        
        async def capture_save(log):
            nonlocal saved_log
            saved_log = log
            return log
        
        repository_mock.save = AsyncMock(side_effect=capture_save)
        
        service = AuditService(repository_mock)
        
        await service.log_admin_action(
            client_id="client-123",
            event_type=AuditEventType.USER_DEACTIVATED,
            action="Deactivated user account",
            admin_user_id="admin-123",
            admin_username="admin",
            target_user_id="user-123",
            target_username="john"
        )
        
        assert saved_log is not None
        assert "administrative" in saved_log.tags
        assert "critical" in saved_log.tags


@pytest.mark.unit
class TestQueryMethods:
    """Test audit log query methods"""
    
    @pytest.mark.asyncio
    async def test_get_user_audit_logs_calls_repository(self):
        """Test get_user_audit_logs delegates to repository"""
        repository_mock = AsyncMock()
        repository_mock.find_by_user = AsyncMock(return_value=[])
        
        service = AuditService(repository_mock)
        
        result = await service.get_user_audit_logs(
            user_id="user-123",
            client_id="client-123",
            days=30
        )
        
        repository_mock.find_by_user.assert_called_once()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_entity_audit_trail_calls_repository(self):
        """Test get_entity_audit_trail delegates to repository"""
        repository_mock = AsyncMock()
        repository_mock.find_by_entity = AsyncMock(return_value=[])
        
        service = AuditService(repository_mock)
        
        result = await service.get_entity_audit_trail(
            entity_type="project",
            entity_id="proj-123"
        )
        
        repository_mock.find_by_entity.assert_called_once()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_recent_events_calls_repository(self):
        """Test get_recent_events delegates to repository"""
        repository_mock = AsyncMock()
        repository_mock.find_recent = AsyncMock(return_value=[])
        
        service = AuditService(repository_mock)
        
        result = await service.get_recent_events(
            client_id="client-123",
            limit=50
        )
        
        repository_mock.find_recent.assert_called_once()
        assert isinstance(result, list)


@pytest.mark.unit
class TestSecurityDetection:
    """Test security detection methods"""
    
    @pytest.mark.asyncio
    async def test_detect_brute_force_identifies_attacks(self):
        """Test brute force detection identifies attack patterns"""
        repository_mock = AsyncMock()
        repository_mock.count_failed_logins = AsyncMock(return_value=10)
        
        service = AuditService(repository_mock)
        
        is_attack = await service.detect_brute_force(
            user_id="user-123",
            threshold=5,
            minutes=30
        )
        
        assert is_attack is True
    
    @pytest.mark.asyncio
    async def test_detect_brute_force_normal_activity(self):
        """Test brute force detection allows normal activity"""
        repository_mock = AsyncMock()
        repository_mock.count_failed_logins = AsyncMock(return_value=2)
        
        service = AuditService(repository_mock)
        
        is_attack = await service.detect_brute_force(
            user_id="user-123",
            threshold=5,
            minutes=30
        )
        
        assert is_attack is False

