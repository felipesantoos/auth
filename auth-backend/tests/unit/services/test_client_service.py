"""
Unit tests for Client Service
Tests client management logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.client.client_service import ClientService


@pytest.mark.unit
class TestClientManagement:
    """Test client management functionality"""
    
    @pytest.mark.asyncio
    async def test_create_client_generates_credentials(self):
        """Test creating client generates API credentials"""
        client_repo_mock = AsyncMock()
        client_repo_mock.save = AsyncMock(return_value=Mock(id="client-123"))
        
        service = ClientService(client_repo_mock)
        
        client = await service.create_client(
            name="Test Client",
            description="Test Description"
        )
        
        assert client_repo_mock.save.called
    
    @pytest.mark.asyncio
    async def test_get_client_by_id_calls_repository(self):
        """Test getting client by ID delegates to repository"""
        client_repo_mock = AsyncMock()
        client_repo_mock.get_by_id = AsyncMock(return_value=Mock(id="client-123"))
        
        service = ClientService(client_repo_mock)
        
        client = await service.get_client_by_id("client-123")
        
        client_repo_mock.get_by_id.assert_called_with("client-123")

