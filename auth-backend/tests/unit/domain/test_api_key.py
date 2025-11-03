"""
Unit tests for ApiKey domain model
Tests API key validation and security logic
"""
import pytest
from datetime import datetime, timedelta
from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope
from core.exceptions import (
    MissingRequiredFieldException,
    InvalidValueException,
    BusinessRuleException,
)
from tests.factories import ApiKeyFactory


@pytest.mark.unit
class TestApiKeyValidation:
    """Test ApiKey validation rules"""
    
    def test_valid_api_key_passes_validation(self):
        """Test that a valid API key passes validation"""
        api_key = ApiKeyFactory.build()
        # Should not raise
        api_key.validate()
    
    def test_missing_client_id_raises_exception(self):
        """Test that missing client_id raises exception"""
        api_key = ApiKeyFactory.build(client_id="")
        
        with pytest.raises(MissingRequiredFieldException, match="client_id"):
            api_key.validate()
    
    def test_name_too_short_raises_exception(self):
        """Test that name shorter than 3 chars raises exception"""
        api_key = ApiKeyFactory.build(name="ab")
        
        with pytest.raises(InvalidValueException, match="at least 3 characters"):
            api_key.validate()
    
    def test_name_too_long_raises_exception(self):
        """Test that name longer than 100 chars raises exception"""
        api_key = ApiKeyFactory.build(name="a" * 101)
        
        with pytest.raises(InvalidValueException, match="not exceed 100 characters"):
            api_key.validate()
    
    def test_missing_key_hash_raises_exception(self):
        """Test that missing key_hash raises exception"""
        api_key = ApiKeyFactory.build()
        api_key.key_hash = ""
        
        with pytest.raises(MissingRequiredFieldException, match="key_hash"):
            api_key.validate()
    
    def test_empty_scopes_raises_exception(self):
        """Test that empty scopes list raises exception"""
        api_key = ApiKeyFactory.build(scopes=[])
        
        with pytest.raises(InvalidValueException, match="at least one scope"):
            api_key.validate()


@pytest.mark.unit
class TestApiKeyIsActive:
    """Test ApiKey.is_active() method"""
    
    def test_is_active_returns_true_for_valid_key(self):
        """Test is_active returns True for non-revoked, non-expired key"""
        api_key = ApiKeyFactory.build(
            revoked_at=None,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert api_key.is_active() is True
    
    def test_is_active_returns_false_for_revoked_key(self):
        """Test is_active returns False for revoked key"""
        api_key = ApiKeyFactory.create_revoked_key(user_id="user-123")
        
        assert api_key.is_active() is False
    
    def test_is_active_returns_false_for_expired_key(self):
        """Test is_active returns False for expired key"""
        api_key = ApiKeyFactory.create_expired_key(user_id="user-123")
        
        assert api_key.is_active() is False
    
    def test_is_active_returns_true_for_key_without_expiration(self):
        """Test is_active returns True for key without expiration"""
        api_key = ApiKeyFactory.build(
            revoked_at=None,
            expires_at=None  # Never expires
        )
        
        assert api_key.is_active() is True


@pytest.mark.unit
class TestApiKeyExpiration:
    """Test API key expiration logic"""
    
    def test_is_expired_returns_false_for_future_expiration(self):
        """Test is_expired returns False when expiration is in future"""
        api_key = ApiKeyFactory.build(
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert api_key.is_expired() is False
    
    def test_is_expired_returns_true_for_past_expiration(self):
        """Test is_expired returns True when expiration is in past"""
        api_key = ApiKeyFactory.create_expired_key(user_id="user-123")
        
        assert api_key.is_expired() is True
    
    def test_is_expired_returns_false_when_no_expiration(self):
        """Test is_expired returns False when expires_at is None"""
        api_key = ApiKeyFactory.build(expires_at=None)
        
        assert api_key.is_expired() is False


@pytest.mark.unit
class TestApiKeyRevocation:
    """Test API key revocation"""
    
    def test_is_revoked_returns_false_for_active_key(self):
        """Test is_revoked returns False for non-revoked key"""
        api_key = ApiKeyFactory.build(revoked_at=None)
        
        assert api_key.is_revoked() is False
    
    def test_is_revoked_returns_true_for_revoked_key(self):
        """Test is_revoked returns True for revoked key"""
        api_key = ApiKeyFactory.create_revoked_key(user_id="user-123")
        
        assert api_key.is_revoked() is True
    
    def test_revoke_sets_revoked_at(self):
        """Test revoke() sets revoked_at timestamp"""
        api_key = ApiKeyFactory.build()
        
        api_key.revoke()
        
        assert api_key.revoked_at is not None
        assert isinstance(api_key.revoked_at, datetime)
    
    def test_revoke_already_revoked_raises_exception(self):
        """Test revoking already revoked key raises exception"""
        api_key = ApiKeyFactory.create_revoked_key(user_id="user-123")
        
        with pytest.raises(BusinessRuleException, match="already been revoked"):
            api_key.revoke()


@pytest.mark.unit
class TestApiKeyLastUsed:
    """Test API key last used tracking"""
    
    def test_update_last_used_sets_timestamp(self):
        """Test update_last_used() sets last_used_at"""
        api_key = ApiKeyFactory.build()
        
        assert api_key.last_used_at is None
        
        api_key.update_last_used()
        
        assert api_key.last_used_at is not None
        assert isinstance(api_key.last_used_at, datetime)
    
    def test_update_last_used_updates_existing_timestamp(self):
        """Test update_last_used() updates existing timestamp"""
        api_key = ApiKeyFactory.build(
            last_used_at=datetime.utcnow() - timedelta(days=1)
        )
        old_timestamp = api_key.last_used_at
        
        api_key.update_last_used()
        
        assert api_key.last_used_at > old_timestamp


@pytest.mark.unit
class TestApiKeyScopes:
    """Test API key scope checking"""
    
    def test_has_scope_returns_true_for_matching_scope(self):
        """Test has_scope returns True when key has the scope"""
        api_key = ApiKeyFactory.build(scopes=[ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER])
        
        assert api_key.has_scope(ApiKeyScope.READ_USER) is True
        assert api_key.has_scope(ApiKeyScope.WRITE_USER) is True
    
    def test_has_scope_returns_false_for_missing_scope(self):
        """Test has_scope returns False when key doesn't have the scope"""
        api_key = ApiKeyFactory.build(scopes=[ApiKeyScope.READ_USER])
        
        assert api_key.has_scope(ApiKeyScope.WRITE_USER) is False
        assert api_key.has_scope(ApiKeyScope.DELETE_USER) is False
    
    def test_has_scope_with_admin_always_returns_true(self):
        """Test ADMIN scope grants all permissions"""
        api_key = ApiKeyFactory.create_admin_key(user_id="user-123")
        
        # Admin scope should grant all scopes
        assert api_key.has_scope(ApiKeyScope.READ_USER) is True
        assert api_key.has_scope(ApiKeyScope.WRITE_USER) is True
        assert api_key.has_scope(ApiKeyScope.DELETE_USER) is True
    
    def test_has_any_scope_returns_true_when_has_one(self):
        """Test has_any_scope returns True when key has at least one scope"""
        api_key = ApiKeyFactory.build(scopes=[ApiKeyScope.READ_USER])
        
        result = api_key.has_any_scope([ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER])
        assert result is True
    
    def test_has_any_scope_returns_false_when_has_none(self):
        """Test has_any_scope returns False when key has none of the scopes"""
        api_key = ApiKeyFactory.build(scopes=[ApiKeyScope.READ_USER])
        
        result = api_key.has_any_scope([ApiKeyScope.WRITE_USER, ApiKeyScope.DELETE_USER])
        assert result is False
    
    def test_has_all_scopes_returns_true_when_has_all(self):
        """Test has_all_scopes returns True when key has all scopes"""
        api_key = ApiKeyFactory.build(
            scopes=[ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER, ApiKeyScope.DELETE_USER]
        )
        
        result = api_key.has_all_scopes([ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER])
        assert result is True
    
    def test_has_all_scopes_returns_false_when_missing_one(self):
        """Test has_all_scopes returns False when key is missing a scope"""
        api_key = ApiKeyFactory.build(scopes=[ApiKeyScope.READ_USER])
        
        result = api_key.has_all_scopes([ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER])
        assert result is False
    
    def test_get_scopes_list_returns_string_values(self):
        """Test get_scopes_list returns scope values as strings"""
        api_key = ApiKeyFactory.build(
            scopes=[ApiKeyScope.READ_USER, ApiKeyScope.WRITE_USER]
        )
        
        scopes_list = api_key.get_scopes_list()
        
        assert isinstance(scopes_list, list)
        assert all(isinstance(s, str) for s in scopes_list)
        assert "read:user" in scopes_list
        assert "write:user" in scopes_list


@pytest.mark.unit
class TestApiKeyGeneration:
    """Test API key generation"""
    
    def test_generate_key_creates_key_with_prefix(self):
        """Test generate_key creates key with 'ask_' prefix"""
        key = ApiKey.generate_key()
        
        assert key.startswith("ask_")
        assert len(key) > 10
    
    def test_generate_key_creates_unique_keys(self):
        """Test generate_key creates unique keys"""
        key1 = ApiKey.generate_key()
        key2 = ApiKey.generate_key()
        
        assert key1 != key2

