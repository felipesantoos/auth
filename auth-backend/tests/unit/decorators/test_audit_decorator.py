"""
Unit tests for Audit Decorator
Tests automatic audit logging decorators without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.decorators.audit_decorator import audit_entity_change, audit_data_access
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.entity_change import EntityChange


@pytest.mark.unit
class TestAuditEntityChangeDecorator:
    """Test @audit_entity_change decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_logs_entity_creation(self):
        """Test decorator logs entity creation event"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_entity_change = AsyncMock()
        
        current_user_mock = Mock(
            id="user-123",
            username="john",
            email="john@example.com",
            client_id="client-123"
        )
        
        @audit_entity_change(
            event_type=AuditEventType.ENTITY_CREATED,
            entity_type="project",
            entity_id_param="project_id"
        )
        async def create_project(project_id: str, audit_service=None, current_user=None):
            return Mock(id=project_id, name="New Project")
        
        result = await create_project(
            project_id="proj-123",
            audit_service=audit_service_mock,
            current_user=current_user_mock
        )
        
        audit_service_mock.log_entity_change.assert_called_once()
        assert result.id == "proj-123"
    
    @pytest.mark.asyncio
    async def test_decorator_detects_changes_on_update(self):
        """Test decorator detects field-level changes on update"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_entity_change = AsyncMock()
        
        current_user_mock = Mock(
            id="user-123",
            username="john",
            client_id="client-123"
        )
        
        old_entity = Mock(id="proj-123", name="Old Name", status="active")
        new_entity = Mock(id="proj-123", name="New Name", status="active")
        
        repository_mock = AsyncMock()
        repository_mock.find_by_id = AsyncMock(return_value=old_entity)
        
        @audit_entity_change(
            event_type=AuditEventType.ENTITY_UPDATED,
            entity_type="project",
            entity_id_param="project_id",
            track_changes=True
        )
        async def update_project(project_id: str, audit_service=None, current_user=None, repository=None):
            return new_entity
        
        result = await update_project(
            project_id="proj-123",
            audit_service=audit_service_mock,
            current_user=current_user_mock,
            repository=repository_mock
        )
        
        # Should log with detected changes
        audit_service_mock.log_entity_change.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_executes_function_without_audit_service(self):
        """Test decorator still executes function if no audit service provided"""
        
        @audit_entity_change(
            event_type=AuditEventType.ENTITY_CREATED,
            entity_type="test"
        )
        async def test_func():
            return "result"
        
        # Should not raise even without audit_service
        result = await test_func()
        
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_decorator_handles_audit_errors_gracefully(self):
        """Test decorator doesn't fail main operation if audit fails"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_entity_change = AsyncMock(side_effect=Exception("Audit DB error"))
        
        current_user_mock = Mock(
            id="user-123",
            username="john",
            client_id="client-123"
        )
        
        @audit_entity_change(
            event_type=AuditEventType.ENTITY_CREATED,
            entity_type="project"
        )
        async def create_project(audit_service=None, current_user=None):
            return Mock(id="proj-123", name="Project")
        
        # Should not raise even if audit fails
        result = await create_project(
            audit_service=audit_service_mock,
            current_user=current_user_mock
        )
        
        assert result.id == "proj-123"


@pytest.mark.unit
class TestAuditDataAccessDecorator:
    """Test @audit_data_access decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_logs_data_access(self):
        """Test decorator logs data access event"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_data_access = AsyncMock()
        
        current_user_mock = Mock(
            id="user-123",
            username="john",
            client_id="client-123"
        )
        
        @audit_data_access(
            access_type="view",
            resource_type="document",
            is_sensitive=True
        )
        async def view_document(doc_id: str, audit_service=None, current_user=None):
            return Mock(id=doc_id, name="Sensitive Document")
        
        result = await view_document(
            doc_id="doc-123",
            audit_service=audit_service_mock,
            current_user=current_user_mock
        )
        
        audit_service_mock.log_data_access.assert_called_once()
        assert result.id == "doc-123"
    
    @pytest.mark.asyncio
    async def test_decorator_marks_sensitive_data_access(self):
        """Test decorator properly marks sensitive data access"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_data_access = AsyncMock()
        
        current_user_mock = Mock(
            id="user-123",
            username="john",
            client_id="client-123"
        )
        
        @audit_data_access(
            access_type="view",
            resource_type="medical_record",
            is_sensitive=True
        )
        async def view_medical_record(record_id: str, audit_service=None, current_user=None):
            return Mock(id=record_id, name="Patient Record")
        
        result = await view_medical_record(
            record_id="rec-123",
            audit_service=audit_service_mock,
            current_user=current_user_mock
        )
        
        # Verify is_sensitive was passed
        call_args = audit_service_mock.log_data_access.call_args
        assert call_args[1]["is_sensitive"] is True
    
    @pytest.mark.asyncio
    async def test_decorator_works_without_audit_service(self):
        """Test decorator works even without audit service"""
        
        @audit_data_access(
            access_type="view",
            resource_type="document"
        )
        async def view_doc():
            return Mock(id="doc-123", name="Document")
        
        result = await view_doc()
        
        assert result.id == "doc-123"

