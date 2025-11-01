"""
Unit tests for ClientMapper
Tests conversion between client domain models and DTOs
"""
import pytest
from datetime import datetime
from app.api.mappers.client_mapper import ClientMapper
from app.api.dtos.response.client_response import ClientResponse, ClientResponseWithApiKey
from tests.factories import ClientFactory


@pytest.mark.unit
class TestClientMapperToResponse:
    """Test converting Client domain to response DTOs"""
    
    def test_to_response_without_api_key_returns_basic_response(self):
        """Test to_response without API key returns ClientResponse"""
        client = ClientFactory.create(
            id="client-123",
            name="Test Company",
            subdomain="test-company",
            active=True,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            updated_at=datetime(2023, 6, 1, 12, 0, 0)
        )
        
        response = ClientMapper.to_response(client, include_api_key=False)
        
        assert isinstance(response, ClientResponse)
        assert response.id == "client-123"
        assert response.name == "Test Company"
        assert response.subdomain == "test-company"
        assert response.active is True
        assert response.created_at == datetime(2023, 1, 1, 12, 0, 0)
        assert response.updated_at == datetime(2023, 6, 1, 12, 0, 0)
        
        # Should not have api_key attribute in basic response
        assert not hasattr(response, 'api_key') or response.api_key is None
    
    def test_to_response_with_api_key_returns_extended_response(self):
        """Test to_response with API key returns ClientResponseWithApiKey"""
        client = ClientFactory.create()
        api_key = client.api_key
        
        response = ClientMapper.to_response(client, include_api_key=True)
        
        assert isinstance(response, ClientResponseWithApiKey)
        assert response.api_key == api_key
        assert len(response.api_key) > 0
    
    def test_to_response_defaults_to_excluding_api_key(self):
        """Test to_response defaults to not including API key"""
        client = ClientFactory.create()
        
        response = ClientMapper.to_response(client)
        
        assert isinstance(response, ClientResponse)
    
    def test_to_response_maps_all_basic_fields(self):
        """Test all basic fields are mapped correctly"""
        client = ClientFactory.create(
            id="client-abc",
            name="Acme Corp",
            subdomain="acme",
            active=True
        )
        
        response = ClientMapper.to_response(client)
        
        assert response.id == "client-abc"
        assert response.name == "Acme Corp"
        assert response.subdomain == "acme"
        assert response.active is True
    
    def test_to_response_preserves_active_status(self):
        """Test active status is preserved"""
        active_client = ClientFactory.create(active=True)
        inactive_client = ClientFactory.create(active=False)
        
        active_response = ClientMapper.to_response(active_client)
        inactive_response = ClientMapper.to_response(inactive_client)
        
        assert active_response.active is True
        assert inactive_response.active is False


@pytest.mark.unit
class TestClientMapperWithApiKey:
    """Test mapper with API key inclusion"""
    
    def test_response_with_api_key_includes_all_basic_fields(self):
        """Test response with API key still includes all basic fields"""
        client = ClientFactory.create(
            id="client-123",
            name="Test Co",
            subdomain="test",
            active=True
        )
        
        response = ClientMapper.to_response(client, include_api_key=True)
        
        # Should have all basic fields
        assert response.id == "client-123"
        assert response.name == "Test Co"
        assert response.subdomain == "test"
        assert response.active is True
        
        # Plus API key
        assert hasattr(response, 'api_key')
        assert response.api_key is not None
    
    def test_to_response_with_api_key_when_client_has_no_key(self):
        """Test to_response handles missing API key gracefully"""
        client = ClientFactory.create()
        # Set API key to None
        client._api_key = None
        
        # Even with include_api_key=True, should handle gracefully
        response = ClientMapper.to_response(client, include_api_key=True)
        
        # Should return basic response since no API key
        assert isinstance(response, ClientResponse)


@pytest.mark.unit
class TestClientMapperNullHandling:
    """Test mapper handles null/None values correctly"""
    
    def test_to_response_handles_none_created_at(self):
        """Test mapper handles None created_at"""
        client = ClientFactory.create(created_at=None)
        
        response = ClientMapper.to_response(client)
        
        assert response.created_at is None
    
    def test_to_response_handles_none_updated_at(self):
        """Test mapper handles None updated_at"""
        client = ClientFactory.create(updated_at=None)
        
        response = ClientMapper.to_response(client)
        
        assert response.updated_at is None
    
    def test_to_response_handles_none_id(self):
        """Test mapper handles None id (before persistence)"""
        client = ClientFactory.create(id=None)
        
        response = ClientMapper.to_response(client)
        
        assert response.id is None


@pytest.mark.unit
class TestClientMapperConsistency:
    """Test mapper produces consistent results"""
    
    def test_same_client_produces_same_response(self):
        """Test mapping same client twice produces same result"""
        client = ClientFactory.create()
        
        response1 = ClientMapper.to_response(client)
        response2 = ClientMapper.to_response(client)
        
        assert response1.id == response2.id
        assert response1.name == response2.name
        assert response1.subdomain == response2.subdomain
        assert response1.active == response2.active
    
    def test_different_clients_produce_different_responses(self):
        """Test mapping different clients produces different results"""
        client1 = ClientFactory.create(name="Client 1", subdomain="client1")
        client2 = ClientFactory.create(name="Client 2", subdomain="client2")
        
        response1 = ClientMapper.to_response(client1)
        response2 = ClientMapper.to_response(client2)
        
        assert response1.name != response2.name
        assert response1.subdomain != response2.subdomain

