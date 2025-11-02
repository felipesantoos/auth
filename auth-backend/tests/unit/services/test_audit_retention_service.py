"""
Unit tests for Audit Retention Service
Tests retention policies and archival logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from core.services.audit.audit_retention_service import AuditRetentionService
from core.domain.audit.audit_event_category import AuditEventCategory


@pytest.mark.unit
class TestAuditRetentionPolicies:
    """Test retention policy configuration"""
    
    def test_authentication_retention_policy(self):
        """Test authentication logs retain for 365 days"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        retention = service.get_retention_days(AuditEventCategory.AUTHENTICATION)
        
        assert retention == 365
    
    def test_authorization_retention_policy(self):
        """Test authorization logs retain for 730 days"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        retention = service.get_retention_days(AuditEventCategory.AUTHORIZATION)
        
        assert retention == 730
    
    def test_data_modification_retention_policy(self):
        """Test data modification logs retain for 2555 days (SOX compliance)"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        retention = service.get_retention_days(AuditEventCategory.DATA_MODIFICATION)
        
        assert retention == 2555
    
    def test_system_retention_policy(self):
        """Test system logs retain for 90 days"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        retention = service.get_retention_days(AuditEventCategory.SYSTEM)
        
        assert retention == 90


@pytest.mark.unit
class TestRetentionCompliance:
    """Test retention compliance checks"""
    
    def test_is_retention_compliant_within_period(self):
        """Test log within retention period is compliant"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        # Log is 100 days old, retention is 365 days
        is_compliant = service.is_retention_compliant(
            AuditEventCategory.AUTHENTICATION,
            100
        )
        
        assert is_compliant is True
    
    def test_is_retention_compliant_beyond_period(self):
        """Test log beyond retention period is not compliant"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        # Log is 400 days old, retention is 365 days
        is_compliant = service.is_retention_compliant(
            AuditEventCategory.AUTHENTICATION,
            400
        )
        
        assert is_compliant is False
    
    def test_is_retention_compliant_exactly_at_limit(self):
        """Test log exactly at retention limit is compliant"""
        repository_mock = Mock()
        service = AuditRetentionService(repository_mock)
        
        # Log is 365 days old, retention is 365 days
        is_compliant = service.is_retention_compliant(
            AuditEventCategory.AUTHENTICATION,
            365
        )
        
        assert is_compliant is True


@pytest.mark.unit
class TestRetentionReport:
    """Test retention report generation"""
    
    @pytest.mark.asyncio
    async def test_get_retention_report_generates_report(self):
        """Test retention report is generated with all categories"""
        repository_mock = AsyncMock()
        repository_mock.count_logs = AsyncMock(return_value=10)
        
        service = AuditRetentionService(repository_mock)
        
        report = await service.get_retention_report()
        
        assert "generated_at" in report
        assert "categories" in report
        assert "total_logs_to_archive" in report
        assert len(report["categories"]) == 7  # All categories
    
    @pytest.mark.asyncio
    async def test_get_retention_report_calculates_totals(self):
        """Test retention report calculates correct totals"""
        repository_mock = AsyncMock()
        repository_mock.count_logs = AsyncMock(return_value=10)
        
        service = AuditRetentionService(repository_mock)
        
        report = await service.get_retention_report()
        
        # 7 categories * 10 logs each = 70 total
        assert report["total_logs_to_archive"] == 70
    
    @pytest.mark.asyncio
    async def test_get_retention_report_with_client_filter(self):
        """Test retention report can filter by client"""
        repository_mock = AsyncMock()
        repository_mock.count_logs = AsyncMock(return_value=5)
        
        service = AuditRetentionService(repository_mock)
        
        report = await service.get_retention_report(client_id="client-123")
        
        assert report["client_id"] == "client-123"
        repository_mock.count_logs.assert_called()


@pytest.mark.unit
class TestArchiveOldLogs:
    """Test log archival"""
    
    @pytest.mark.asyncio
    async def test_archive_dry_run_does_not_delete(self):
        """Test dry run mode does not delete logs"""
        repository_mock = AsyncMock()
        repository_mock.find_by_category = AsyncMock(return_value=[])
        repository_mock.delete_old_logs = AsyncMock()
        
        service = AuditRetentionService(repository_mock)
        
        result = await service.archive_old_logs(dry_run=True)
        
        assert result["dry_run"] is True
        repository_mock.delete_old_logs.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_archive_actual_run_deletes_logs(self):
        """Test actual archival deletes old logs"""
        repository_mock = AsyncMock()
        repository_mock.find_by_category = AsyncMock(return_value=[])
        repository_mock.delete_old_logs = AsyncMock(return_value=5)
        
        service = AuditRetentionService(repository_mock)
        
        result = await service.archive_old_logs(
            category=AuditEventCategory.SYSTEM,
            dry_run=False
        )
        
        assert result["dry_run"] is False
        repository_mock.delete_old_logs.assert_called()


@pytest.mark.unit
class TestCleanupOldLogs:
    """Test old log cleanup"""
    
    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_logs_per_category(self):
        """Test cleanup deletes old logs for each category"""
        repository_mock = AsyncMock()
        repository_mock.delete_old_logs = AsyncMock(return_value=10)
        
        service = AuditRetentionService(repository_mock)
        
        result = await service.cleanup_old_logs_by_policy()
        
        # Should call delete for each category
        assert repository_mock.delete_old_logs.call_count == 7
        assert len(result) == 7
    
    @pytest.mark.asyncio
    async def test_cleanup_returns_deletion_counts(self):
        """Test cleanup returns deletion counts per category"""
        repository_mock = AsyncMock()
        repository_mock.delete_old_logs = AsyncMock(return_value=10)
        
        service = AuditRetentionService(repository_mock)
        
        result = await service.cleanup_old_logs_by_policy()
        
        # All categories should have count
        for category in AuditEventCategory:
            assert category.value in result
            assert result[category.value] == 10

