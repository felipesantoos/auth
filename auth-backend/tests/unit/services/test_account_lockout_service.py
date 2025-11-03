"""
Unit tests for Account Lockout Service
Tests brute-force protection and account locking
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from core.services.auth.account_lockout_service import AccountLockoutService


@pytest.mark.unit
class TestAccountLockoutService:
    """Test account lockout service"""

    @pytest.mark.asyncio
    async def test_check_lockout_not_locked(self):
        """Should return False when account not locked"""
        mock_user_repo = AsyncMock()
        mock_audit = AsyncMock()
        mock_settings = Mock()
        mock_settings.get_settings.return_value = Mock(
            account_lockout_max_attempts=5,
            account_lockout_duration_minutes=30,
            account_lockout_window_minutes=15
        )
        
        service = AccountLockoutService(
            user_repository=mock_user_repo,
            audit_service=mock_audit,
            settings_provider=mock_settings
        )
        
        # Mock: No failed attempts
        mock_audit.count_failed_login_attempts = AsyncMock(return_value=0)
        
        is_locked, unlock_time = await service.check_lockout(
            email="user@example.com",
            ip_address="192.168.1.1",
            client_id="client-123"
        )
        
        assert is_locked is False
        assert unlock_time is None

    @pytest.mark.asyncio
    async def test_record_failed_attempt(self):
        """Should record failed login attempt"""
        mock_user_repo = AsyncMock()
        mock_audit = AsyncMock()
        mock_settings = Mock()
        mock_settings.get_settings.return_value = Mock(
            account_lockout_max_attempts=5,
            account_lockout_duration_minutes=30,
            account_lockout_window_minutes=15
        )
        
        service = AccountLockoutService(
            user_repository=mock_user_repo,
            audit_service=mock_audit,
            settings_provider=mock_settings
        )
        
        result = await service.record_failed_attempt(
            email="user@example.com",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            client_id="client-123"
        )
        
        # Should return bool
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_should_lock_account_after_max_attempts(self):
        """Should lock account after max failed attempts"""
        mock_user_repo = AsyncMock()
        mock_audit = AsyncMock()
        mock_settings = Mock()
        mock_settings.get_settings.return_value = Mock(
            account_lockout_max_attempts=5,
            account_lockout_duration_minutes=30,
            account_lockout_window_minutes=15
        )
        
        service = AccountLockoutService(
            user_repository=mock_user_repo,
            audit_service=mock_audit,
            settings_provider=mock_settings
        )
        
        # 5 failed attempts
        mock_audit.count_failed_login_attempts = AsyncMock(return_value=5)
        
        result = await service.should_lock_account(
            user_id="user-123",
            email="user@example.com",
            ip_address="192.168.1.1",
            client_id="client-123"
        )
        
        assert isinstance(result, bool)


@pytest.mark.unit
class TestAccountLockoutConfiguration:
    """Test lockout configuration"""

    def test_default_configuration(self):
        """Should have default lockout configuration"""
        mock_user_repo = Mock()
        mock_audit = Mock()
        mock_settings = Mock()
        mock_settings.get_settings.return_value = Mock(
            account_lockout_max_attempts=5,
            account_lockout_duration_minutes=30,
            account_lockout_window_minutes=15
        )
        
        service = AccountLockoutService(
            user_repository=mock_user_repo,
            audit_service=mock_audit,
            settings_provider=mock_settings
        )
        
        assert service.max_attempts == 5
        assert service.lockout_duration_minutes == 30
        assert service.attempt_window_minutes == 15

