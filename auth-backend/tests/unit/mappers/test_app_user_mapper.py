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
    

@pytest.mark.unit
class TestAppUserMapperToDatabase:
    """Test converting domain model to DB model"""
    
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

