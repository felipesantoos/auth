"""
Unit tests for ApiKeyMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime
from infra.database.mappers.api_key_mapper import ApiKeyMapper
from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope
from infra.database.models.api_key import DBApiKey


@pytest.mark.unit
class TestApiKeyMapperToDomain:
    """Test converting DB model to domain model"""
    
    def test_to_domain_maps_all_fields(self):
        """Test to_domain maps all fields correctly"""
        db_key = DBApiKey(
            id="key-123",
            user_id="user-123",
            client_id="client-123",
            name="Production API Key",
            key_hash="hashed_key_value",
            scopes=["read:user", "write:user"],
            last_used_at=datetime(2023, 1, 15),
            expires_at=datetime(2024, 1, 1),
            created_at=datetime(2023, 1, 1),
            revoked_at=None
        )
        
        domain_key = ApiKeyMapper.to_domain(db_key)
        
        assert isinstance(domain_key, ApiKey)
        assert domain_key.id == "key-123"
        assert domain_key.user_id == "user-123"
        assert domain_key.client_id == "client-123"
        assert domain_key.name == "Production API Key"
        assert domain_key.key_hash == "hashed_key_value"
        assert len(domain_key.scopes) == 2
        assert ApiKeyScope.READ_USER in domain_key.scopes
        assert ApiKeyScope.WRITE_USER in domain_key.scopes
    
    def test_to_domain_converts_scopes_to_enum(self):
        """Test scopes are converted from string to enum"""
        db_key = DBApiKey(
            id="key-123",
            user_id="user-123",
            client_id="client-123",
            name="Test Key",
            key_hash="hash",
            scopes=["admin", "read:audit"]
        )
        
        domain_key = ApiKeyMapper.to_domain(db_key)
        
        assert all(isinstance(scope, ApiKeyScope) for scope in domain_key.scopes)


@pytest.mark.unit
class TestApiKeyMapperToDatabase:
    """Test converting domain model to DB model"""
    
    def test_to_database_maps_all_fields(self):
        """Test to_database maps all fields correctly"""
        domain_key = ApiKey(
            id="key-123",
            user_id="user-123",
            client_id="client-123",
            name="Test API Key",
            key_hash="hashed_key",
            scopes=[ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER],
            last_used_at=datetime(2023, 1, 15),
            expires_at=datetime(2024, 1, 1),
            created_at=datetime(2023, 1, 1),
            revoked_at=None
        )
        
        db_key = ApiKeyMapper.to_database(domain_key)
        
        assert isinstance(db_key, DBApiKey)
        assert db_key.id == "key-123"
        assert db_key.user_id == "user-123"
        assert db_key.name == "Test API Key"
        assert db_key.key_hash == "hashed_key"
        assert db_key.scopes == ["read:user", "write:user"]
    
    def test_to_database_converts_scopes_to_strings(self):
        """Test scopes are converted from enum to string"""
        domain_key = ApiKey(
            id="key-123",
            user_id="user-123",
            client_id="client-123",
            name="Test Key",
            key_hash="hash",
            scopes=[ApiKeyScope.ADMIN, ApiKeyScope.READ_AUDIT]
        )
        
        db_key = ApiKeyMapper.to_database(domain_key)
        
        assert all(isinstance(scope, str) for scope in db_key.scopes)
        assert "admin" in db_key.scopes
        assert "read:audit" in db_key.scopes

