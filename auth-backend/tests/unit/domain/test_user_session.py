"""
Unit tests for UserSession domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime, timedelta
from core.domain.auth.user_session import UserSession
from core.exceptions import MissingRequiredFieldException, BusinessRuleException


@pytest.mark.unit
class TestUserSessionValidation:
    """Test user session validation"""
    
    def test_valid_session_passes_validation(self):
        """Test that a valid session passes validation"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        # Should not raise
        session.validate()
    
    def test_missing_user_id_raises_exception(self):
        """Test that missing user_id raises exception"""
        session = UserSession(
            id="session-123",
            user_id="",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="user_id"):
            session.validate()
    
    def test_missing_client_id_raises_exception(self):
        """Test that missing client_id raises exception"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="",
            refresh_token_hash="hashed_token"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="client_id"):
            session.validate()
    
    def test_missing_refresh_token_hash_raises_exception(self):
        """Test that missing refresh_token_hash raises exception"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash=""
        )
        
        with pytest.raises(MissingRequiredFieldException, match="refresh_token_hash"):
            session.validate()


@pytest.mark.unit
class TestUserSessionStatus:
    """Test session status checks"""
    
    def test_is_active_returns_true_for_active_session(self):
        """Test is_active returns True for active session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert session.is_active() is True
    
    def test_is_active_returns_false_for_revoked_session(self):
        """Test is_active returns False for revoked session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            revoked_at=datetime.utcnow()
        )
        
        assert session.is_active() is False
    
    def test_is_active_returns_false_for_expired_session(self):
        """Test is_active returns False for expired session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert session.is_active() is False
    
    def test_is_expired_returns_true_for_expired_session(self):
        """Test is_expired returns True for expired session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert session.is_expired() is True
    
    def test_is_expired_returns_false_for_active_session(self):
        """Test is_expired returns False for active session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert session.is_expired() is False
    
    def test_is_expired_returns_false_when_no_expiration(self):
        """Test is_expired returns False when no expiration set"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            expires_at=None
        )
        
        assert session.is_expired() is False
    
    def test_is_revoked_returns_true_for_revoked_session(self):
        """Test is_revoked returns True for revoked session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            revoked_at=datetime.utcnow()
        )
        
        assert session.is_revoked() is True
    
    def test_is_revoked_returns_false_for_active_session(self):
        """Test is_revoked returns False for active session"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        assert session.is_revoked() is False


@pytest.mark.unit
class TestUserSessionActivity:
    """Test session activity tracking"""
    
    def test_update_activity_sets_last_activity(self):
        """Test update_activity sets last_activity timestamp"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        session.update_activity()
        
        assert session.last_activity is not None
        assert isinstance(session.last_activity, datetime)
    
    def test_update_activity_updates_timestamp(self):
        """Test update_activity updates timestamp on subsequent calls"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            last_activity=datetime.utcnow() - timedelta(hours=1)
        )
        
        old_activity = session.last_activity
        session.update_activity()
        
        assert session.last_activity > old_activity


@pytest.mark.unit
class TestUserSessionRevocation:
    """Test session revocation"""
    
    def test_revoke_sets_revoked_at(self):
        """Test revoke sets revoked_at timestamp"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        session.revoke()
        
        assert session.revoked_at is not None
        assert isinstance(session.revoked_at, datetime)
    
    def test_revoke_raises_exception_if_already_revoked(self):
        """Test revoke raises exception if session already revoked"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            revoked_at=datetime.utcnow()
        )
        
        with pytest.raises(BusinessRuleException, match="already been revoked"):
            session.revoke()


@pytest.mark.unit
class TestUserSessionDeviceDescription:
    """Test device description methods"""
    
    def test_get_device_description_returns_device_name_if_set(self):
        """Test get_device_description returns device_name if set"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            device_name="iPhone 13 Pro"
        )
        
        description = session.get_device_description()
        
        assert description == "iPhone 13 Pro"
    
    def test_get_device_description_returns_device_type_if_no_name(self):
        """Test get_device_description returns device_type if no name"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            device_type="mobile"
        )
        
        description = session.get_device_description()
        
        assert description == "Mobile"
    
    def test_get_device_description_returns_unknown_if_no_info(self):
        """Test get_device_description returns Unknown if no info"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        description = session.get_device_description()
        
        assert description == "Unknown Device"
    
    def test_get_location_description_returns_location_if_set(self):
        """Test get_location_description returns location if set"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            location="São Paulo, Brazil"
        )
        
        location = session.get_location_description()
        
        assert location == "São Paulo, Brazil"
    
    def test_get_location_description_returns_unknown_if_not_set(self):
        """Test get_location_description returns Unknown if not set"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token"
        )
        
        location = session.get_location_description()
        
        assert location == "Unknown Location"


@pytest.mark.unit
class TestUserSessionOptionalFields:
    """Test optional session fields"""
    
    def test_session_can_have_user_agent(self):
        """Test session can have user_agent"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        
        assert session.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    
    def test_session_can_have_ip_address(self):
        """Test session can have ip_address"""
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            ip_address="192.168.1.1"
        )
        
        assert session.ip_address == "192.168.1.1"
    
    def test_session_can_have_created_at(self):
        """Test session can have created_at"""
        created = datetime.utcnow()
        session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            created_at=created
        )
        
        assert session.created_at == created

