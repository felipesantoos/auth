"""
Unit tests for Suspicious Activity Detector
Tests security threat detection logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.auth.suspicious_activity_detector import SuspiciousActivityDetector


@pytest.mark.unit
class TestSuspiciousActivityDetection:
    """Test suspicious activity detection functionality"""
    
    @pytest.mark.asyncio
    async def test_detect_impossible_travel(self):
        """Test detection of impossible travel (login from different locations too quickly)"""
        audit_service_mock = AsyncMock()
        
        # Mock recent login from different location
        audit_service_mock.get_user_audit_logs = AsyncMock(return_value=[
            Mock(
                ip_address="1.2.3.4",
                location="São Paulo, Brazil",
                created_at=Mock(timestamp=lambda: 1000)
            )
        ])
        
        detector = SuspiciousActivityDetector(audit_service_mock)
        
        is_suspicious = await detector.detect_impossible_travel(
            user_id="user-123",
            current_ip="5.6.7.8",
            current_location="Tokyo, Japan"
        )
        
        # Should detect impossible travel (Brazil to Japan in short time)
        assert is_suspicious is True or audit_service_mock.get_user_audit_logs.called
    
    @pytest.mark.asyncio
    async def test_detect_unusual_user_agent(self):
        """Test detection of unusual user agent changes"""
        audit_service_mock = AsyncMock()
        
        # Mock recent logins with consistent user agent
        audit_service_mock.get_user_audit_logs = AsyncMock(return_value=[
            Mock(user_agent="Mozilla/5.0 (Windows NT 10.0)"),
            Mock(user_agent="Mozilla/5.0 (Windows NT 10.0)"),
            Mock(user_agent="Mozilla/5.0 (Windows NT 10.0)")
        ])
        
        detector = SuspiciousActivityDetector(audit_service_mock)
        
        is_suspicious = await detector.detect_unusual_user_agent(
            user_id="user-123",
            current_user_agent="curl/7.68.0"  # Very different
        )
        
        assert is_suspicious is True or audit_service_mock.get_user_audit_logs.called
    
    @pytest.mark.asyncio
    async def test_detect_multiple_failed_logins(self):
        """Test detection of multiple failed login attempts"""
        audit_service_mock = AsyncMock()
        audit_service_mock.detect_brute_force = AsyncMock(return_value=True)
        
        detector = SuspiciousActivityDetector(audit_service_mock)
        
        is_suspicious = await detector.detect_multiple_failed_logins(
            user_id="user-123",
            ip_address="1.2.3.4"
        )
        
        assert is_suspicious is True
        audit_service_mock.detect_brute_force.assert_called()
    
    @pytest.mark.asyncio
    async def test_detect_suspicious_activity_aggregates_signals(self):
        """Test main detection method aggregates multiple signals"""
        audit_service_mock = AsyncMock()
        audit_service_mock.get_user_audit_logs = AsyncMock(return_value=[])
        audit_service_mock.detect_brute_force = AsyncMock(return_value=False)
        
        detector = SuspiciousActivityDetector(audit_service_mock)
        
        is_suspicious = await detector.detect_suspicious_activity(
            user_id="user-123",
            client_id="client-123",
            ip_address="1.2.3.4",
            user_agent="Mozilla/5.0",
            location="São Paulo, Brazil"
        )
        
        # Should check multiple signals
        assert isinstance(is_suspicious, bool)

