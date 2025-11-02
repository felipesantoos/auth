"""
Unit tests for Account Lockout Service
Tests account lockout logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from core.services.auth.account_lockout_service import AccountLockoutService


@pytest.mark.unit
class TestAccountLockout:
    """Test account lockout functionality"""
    
    @pytest.mark.asyncio
    async def test_record_failed_login_increments_counter(self):
        """Test recording failed login increments counter"""
        user_repo_mock = AsyncMock()
        cache_mock = Mock()
        cache_mock.get = Mock(return_value="2")
        cache_mock.set = Mock()
        
        service = AccountLockoutService(user_repo_mock, cache_mock)
        
        await service.record_failed_login("user-123")
        
        cache_mock.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_should_lock_account_after_threshold(self):
        """Test account is locked after exceeding threshold"""
        user_repo_mock = AsyncMock()
        cache_mock = Mock()
        cache_mock.get = Mock(return_value="5")  # 5 failed attempts
        
        service = AccountLockoutService(user_repo_mock, cache_mock)
        
        should_lock = await service.should_lock_account("user-123", threshold=3)
        
        assert should_lock is True
    
    @pytest.mark.asyncio
    async def test_reset_failed_attempts_clears_counter(self):
        """Test resetting failed attempts clears counter"""
        user_repo_mock = AsyncMock()
        cache_mock = Mock()
        cache_mock.delete = Mock()
        
        service = AccountLockoutService(user_repo_mock, cache_mock)
        
        await service.reset_failed_attempts("user-123")
        
        cache_mock.delete.assert_called()

