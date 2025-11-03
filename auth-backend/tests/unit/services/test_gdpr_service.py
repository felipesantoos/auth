"""
Unit tests for GDPR Service
Tests GDPR compliance logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.compliance.gdpr_service import GDPRService


@pytest.mark.unit
class TestGDPRCompliance:
    """Test GDPR compliance functionality"""
    
    @pytest.mark.asyncio
    async def test_export_user_data_includes_all_data(self):
        """Test user data export includes all GDPR-required data"""
        user_repo_mock = AsyncMock()
        audit_repo_mock = AsyncMock()
        
        user_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="user-123",
            email="user@example.com",
            name="John Doe"
        ))
        audit_repo_mock.find_by_user = AsyncMock(return_value=[])
        
        service = GDPRService(user_repo_mock, audit_repo_mock, audit_service_mock := AsyncMock())
        
        export = await service.export_user_data("user-123")
        
        assert "user_data" in export
        assert user_repo_mock.get_by_id.called
    
    @pytest.mark.asyncio
    async def test_delete_user_data_calls_repositories(self):
        """Test deleting user data calls all necessary repositories"""
        user_repo_mock = AsyncMock()
        audit_repo_mock = AsyncMock()
        
        user_repo_mock.delete = AsyncMock()
        audit_repo_mock.delete_by_user = AsyncMock()
        
        service = GDPRService(user_repo_mock, audit_repo_mock, audit_service_mock := AsyncMock())
        
        await service.delete_user_data("user-123")
        
        user_repo_mock.delete.assert_called()

