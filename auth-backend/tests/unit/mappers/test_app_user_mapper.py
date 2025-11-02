"""
Unit tests for AppUserMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime
from infra.database.mappers.app_user_mapper import AppUserMapper
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from infra.database.models.app_user import DBAppUser


@pytest.mark.unit
class TestAppUserMapperToDomain:
    """Test converting DB model to domain model"""
    
    def test_to_domain_maps_all_fields(self):
        """Test to_domain maps all fields correctly"""
        db_user = DBAppUser(
            id="user-123",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="admin",
            active=True,
            client_id="client-123",
            email_verified=True,
            mfa_enabled=False,
            created_at=datetime(2023, 1, 1)
        )
        
        domain_user = AppUserMapper.to_domain(db_user)
        
        assert isinstance(domain_user, AppUser)
        assert domain_user.id == "user-123"
        assert domain_user.username == "testuser"
        assert domain_user.email == "test@example.com"
        assert domain_user.name == "Test User"
        assert domain_user.role == UserRole.ADMIN
        assert domain_user.active is True
        assert domain_user.client_id == "client-123"
    
    def test_to_domain_converts_role_to_enum(self):
        """Test role is converted from string to enum"""
        db_user = DBAppUser(
            id="user-123",
            username="user",
            email="user@example.com",
            password_hash="hash",
            name="User",
            role="manager",
            client_id="client-123"
        )
        
        domain_user = AppUserMapper.to_domain(db_user)
        
        assert domain_user.role == UserRole.MANAGER
        assert isinstance(domain_user.role, UserRole)


@pytest.mark.unit
class TestAppUserMapperToDatabase:
    """Test converting domain model to DB model"""
    
    def test_to_database_maps_all_fields(self):
        """Test to_database maps all fields correctly"""
        domain_user = AppUser(
            id="user-123",
            username="testuser",
            email="test@example.com",
            _password_hash="hashed_password",
            name="Test User",
            role=UserRole.USER,
            active=True,
            client_id="client-123",
            email_verified=False,
            mfa_enabled=True
        )
        
        db_user = AppUserMapper.to_database(domain_user)
        
        assert isinstance(db_user, DBAppUser)
        assert db_user.id == "user-123"
        assert db_user.username == "testuser"
        assert db_user.email == "test@example.com"
        assert db_user.password_hash == "hashed_password"
        assert db_user.role == "user"
        assert db_user.mfa_enabled is True
    
    def test_to_database_converts_role_to_string(self):
        """Test role is converted from enum to string"""
        domain_user = AppUser(
            id="user-123",
            username="admin",
            email="admin@example.com",
            _password_hash="hash",
            name="Admin",
            role=UserRole.ADMIN,
            client_id="client-123"
        )
        
        db_user = AppUserMapper.to_database(domain_user)
        
        assert db_user.role == "admin"
        assert isinstance(db_user.role, str)

