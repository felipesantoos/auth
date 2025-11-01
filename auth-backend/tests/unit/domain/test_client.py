"""
Unit tests for Client domain model
Tests client validation and business logic
"""
import pytest
from core.domain.client.client import Client
from tests.factories import ClientFactory


@pytest.mark.unit
class TestClientValidation:
    """Test Client validation rules"""
    
    def test_valid_client_passes_validation(self):
        """Test that a valid client passes validation"""
        client = ClientFactory.create()
        # Should not raise
        client.validate()
    
    def test_name_too_short_raises_exception(self):
        """Test that name shorter than 3 chars raises exception"""
        client = ClientFactory.create(name="ab")
        
        with pytest.raises(ValueError, match="at least 3 characters"):
            client.validate()
    
    def test_empty_name_raises_exception(self):
        """Test that empty name raises exception"""
        client = ClientFactory.create(name="")
        
        with pytest.raises(ValueError, match="at least 3 characters"):
            client.validate()
    
    def test_subdomain_too_short_raises_exception(self):
        """Test that subdomain shorter than 2 chars raises exception"""
        client = ClientFactory.create(subdomain="a")
        
        with pytest.raises(ValueError, match="at least 2 characters"):
            client.validate()
    
    def test_empty_subdomain_raises_exception(self):
        """Test that empty subdomain raises exception"""
        client = ClientFactory.create(subdomain="")
        
        with pytest.raises(ValueError, match="at least 2 characters"):
            client.validate()
    
    def test_subdomain_with_special_chars_raises_exception(self):
        """Test that subdomain with special characters raises exception"""
        client = ClientFactory.create(subdomain="test@client")
        
        with pytest.raises(ValueError, match="alphanumeric characters and hyphens"):
            client.validate()
    
    def test_subdomain_with_spaces_raises_exception(self):
        """Test that subdomain with spaces raises exception"""
        client = ClientFactory.create(subdomain="test client")
        
        with pytest.raises(ValueError, match="alphanumeric characters and hyphens"):
            client.validate()
    
    def test_subdomain_with_underscores_raises_exception(self):
        """Test that subdomain with underscores raises exception"""
        client = ClientFactory.create(subdomain="test_client")
        
        with pytest.raises(ValueError, match="alphanumeric characters and hyphens"):
            client.validate()
    
    def test_valid_subdomain_with_hyphens_passes(self):
        """Test that subdomain with hyphens is valid"""
        client = ClientFactory.create(subdomain="test-client-123")
        # Should not raise
        client.validate()
    
    def test_valid_subdomain_alphanumeric_passes(self):
        """Test that alphanumeric subdomain is valid"""
        client = ClientFactory.create(subdomain="testclient123")
        # Should not raise
        client.validate()


@pytest.mark.unit
class TestClientActivation:
    """Test client activation/deactivation"""
    
    def test_activate_sets_active_to_true(self):
        """Test activate() sets active to True"""
        client = ClientFactory.create(active=False)
        client.activate()
        assert client.active is True
    
    def test_deactivate_sets_active_to_false(self):
        """Test deactivate() sets active to False"""
        client = ClientFactory.create(active=True)
        client.deactivate()
        assert client.active is False


@pytest.mark.unit
class TestClientApiKey:
    """Test client API key functionality"""
    
    def test_api_key_property_returns_key(self):
        """Test api_key property returns the key"""
        client = ClientFactory.create()
        assert client.api_key is not None
        assert len(client.api_key) > 0
    
    def test_generate_api_key_creates_new_key(self):
        """Test generate_api_key creates a new key"""
        client = Client(
            id="client-123",
            name="Test Client",
            subdomain="test-client"
        )
        
        # Initially no key
        assert client.api_key is None
        
        # Generate key
        new_key = client.generate_api_key()
        
        assert new_key is not None
        assert len(new_key) > 20  # URL-safe tokens are long
        assert client.api_key == new_key
    
    def test_generate_api_key_overwrites_existing_key(self):
        """Test generate_api_key replaces existing key"""
        client = ClientFactory.create()
        old_key = client.api_key
        
        new_key = client.generate_api_key()
        
        assert new_key != old_key
        assert client.api_key == new_key
    
    def test_api_key_cannot_be_set_directly(self):
        """Test api_key property is read-only"""
        client = ClientFactory.create()
        
        # api_key is a property without setter, so direct assignment should fail
        # This is tested by attempting to set it
        with pytest.raises(AttributeError):
            client.api_key = "new-key"


@pytest.mark.unit
class TestClientCreation:
    """Test client creation"""
    
    def test_client_created_with_all_fields(self):
        """Test creating client with all fields"""
        client = Client(
            id="client-123",
            name="Test Company",
            subdomain="test-company",
            active=True
        )
        
        assert client.id == "client-123"
        assert client.name == "Test Company"
        assert client.subdomain == "test-company"
        assert client.active is True
    
    def test_client_defaults_to_active(self):
        """Test client defaults to active=True"""
        client = Client(
            id="client-123",
            name="Test Company",
            subdomain="test-company"
        )
        
        assert client.active is True
    
    def test_client_can_be_created_inactive(self):
        """Test client can be created with active=False"""
        client = Client(
            id="client-123",
            name="Test Company",
            subdomain="test-company",
            active=False
        )
        
        assert client.active is False

