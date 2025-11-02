"""
Unit tests for UserSessionMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime, timedelta
from infra.database.mappers.user_session_mapper import UserSessionMapper
from core.domain.auth.user_session import UserSession
from infra.database.models.user_session import DBUserSession


@pytest.mark.unit
class TestUserSessionMapperToDomain:
    """Test converting DB model to domain model"""
    
    def test_to_domain_maps_all_fields(self):
        """Test to_domain maps all fields correctly"""
        db_session = DBUserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_token",
            device_name="iPhone 13",
            device_type="mobile",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            location="São Paulo, Brazil",
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            revoked_at=None
        )
        
        domain_session = UserSessionMapper.to_domain(db_session)
        
        assert isinstance(domain_session, UserSession)
        assert domain_session.id == "session-123"
        assert domain_session.user_id == "user-123"
        assert domain_session.client_id == "client-123"
        assert domain_session.refresh_token_hash == "hashed_token"
        assert domain_session.device_name == "iPhone 13"
        assert domain_session.device_type == "mobile"
        assert domain_session.ip_address == "192.168.1.1"
        assert domain_session.location == "São Paulo, Brazil"
    
    def test_to_domain_with_revoked_session(self):
        """Test converting revoked session"""
        db_session = DBUserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hash",
            revoked_at=datetime.utcnow()
        )
        
        domain_session = UserSessionMapper.to_domain(db_session)
        
        assert domain_session.revoked_at is not None
        assert domain_session.is_revoked() is True


@pytest.mark.unit
class TestUserSessionMapperToDatabase:
    """Test converting domain model to DB model"""
    
    def test_to_database_maps_all_fields(self):
        """Test to_database maps all fields correctly"""
        domain_session = UserSession(
            id="session-123",
            user_id="user-123",
            client_id="client-123",
            refresh_token_hash="hashed_refresh_token",
            device_name="MacBook Pro",
            device_type="desktop",
            ip_address="10.0.0.1",
            user_agent="Chrome/100.0",
            location="Tokyo, Japan",
            last_activity=datetime.utcnow(),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db_session = UserSessionMapper.to_database(domain_session)
        
        assert isinstance(db_session, DBUserSession)
        assert db_session.id == "session-123"
        assert db_session.user_id == "user-123"
        assert db_session.refresh_token_hash == "hashed_refresh_token"
        assert db_session.device_name == "MacBook Pro"
        assert db_session.location == "Tokyo, Japan"

