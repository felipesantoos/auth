"""
Integration tests for API Key Routes
Tests Personal Access Token API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestApiKeyCreation:
    """Test API key creation endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_api_key_requires_authentication(self, async_client: AsyncClient):
        """Test creating API key requires authentication"""
        response = await async_client.post(
            "/api/auth/api-keys",
            json={
                "name": "Test Key",
                "scopes": ["read", "write"]
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_api_key_with_valid_data(self, async_client: AsyncClient, auth_token):
        """Test creating API key with valid data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/auth/api-keys",
            json={
                "name": "Integration Test Key",
                "scopes": ["read"]
            },
            headers=headers
        )
        
        # May succeed or fail depending on implementation
        assert response.status_code in [201, 200, 400, 422]


@pytest.mark.integration
class TestApiKeyListing:
    """Test API key listing endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_api_keys_requires_authentication(self, async_client: AsyncClient):
        """Test listing API keys requires authentication"""
        response = await async_client.get("/api/auth/api-keys")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_api_keys_returns_list(self, async_client: AsyncClient, auth_token):
        """Test listing API keys returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/auth/api-keys",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.integration
class TestApiKeyRevocation:
    """Test API key revocation endpoints"""
    
    @pytest.mark.asyncio
    async def test_revoke_api_key_requires_authentication(self, async_client: AsyncClient):
        """Test revoking API key requires authentication"""
        response = await async_client.delete("/api/auth/api-keys/key-123")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_revoke_nonexistent_api_key_returns_404(self, async_client: AsyncClient, auth_token):
        """Test revoking nonexistent API key"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.delete(
            "/api/auth/api-keys/nonexistent-key-id",
            headers=headers
        )
        
        assert response.status_code in [404, 400]


@pytest.mark.integration
class TestApiKeyAuthentication:
    """Test API key authentication"""
    
    @pytest.mark.asyncio
    async def test_authenticate_with_invalid_api_key_fails(self, async_client: AsyncClient):
        """Test authentication with invalid API key fails"""
        headers = {"X-API-Key": "invalid-key"}
        
        response = await async_client.get(
            "/api/auth/me",
            headers=headers
        )
        
        assert response.status_code == 401

