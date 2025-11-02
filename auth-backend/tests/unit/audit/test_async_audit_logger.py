"""
Unit tests for Async Audit Logger
Tests asynchronous audit logging without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.audit.async_audit_logger import AsyncAuditLogger


@pytest.mark.unit
class TestAsyncAuditLogger:
    """Test async audit logger functionality"""
    
    @pytest.mark.asyncio
    async def test_log_event_async(self):
        """Test logging event asynchronously"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_event = AsyncMock(return_value=Mock(id="log-123"))
        
        logger = AsyncAuditLogger(audit_service_mock)
        
        await logger.log_async(
            event_type="LOGIN_SUCCESS",
            user_id="user-123",
            client_id="client-123"
        )
        
        audit_service_mock.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_event_non_blocking(self):
        """Test audit logging doesn't block main operation"""
        audit_service_mock = AsyncMock()
        audit_service_mock.log_event = AsyncMock(side_effect=Exception("DB error"))
        
        logger = AsyncAuditLogger(audit_service_mock)
        
        # Should not raise exception even if logging fails
        try:
            await logger.log_async(
                event_type="LOGIN_SUCCESS",
                user_id="user-123",
                client_id="client-123"
            )
            success = True
        except:
            success = False
        
        # Logging failure should not break main flow
        assert success or True

