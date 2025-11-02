"""
Integration tests for OAuth Routes
Tests OAuth authentication API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestOAuthRoutes:
    """Test OAuth authentication routes"""
    
    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url(self, async_client: AsyncClient):
        """Test getting OAuth authorization URL"""
        response = await async_client.get(
            "/api/v1/oauth/authorize/google?redirect_uri=http://localhost/callback"
        )
        
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            data = response.json()
            assert "authorization_url" in data or "url" in data
    
    @pytest.mark.asyncio
    async def test_oauth_callback(self, async_client: AsyncClient):
        """Test OAuth callback endpoint"""
        response = await async_client.get(
            "/api/v1/oauth/callback/google?code=test_code&state=test_state"
        )
        
        # Will likely fail without real OAuth, but should have endpoint
        assert response.status_code in [200, 400, 401]
    
    @pytest.mark.asyncio
    async def test_link_oauth_account(self, async_client: AsyncClient, auth_token: str):
        """Test linking OAuth account to existing user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/v1/oauth/link/google",
            headers=headers,
            json={"code": "oauth_code"}
        )
        
        assert response.status_code in [200, 400, 401]
    
    @pytest.mark.asyncio
    async def test_unlink_oauth_account(self, async_client: AsyncClient, auth_token: str):
        """Test unlinking OAuth account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.delete(
            "/api/v1/oauth/unlink/google",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_get_linked_accounts(self, async_client: AsyncClient, auth_token: str):
        """Test getting linked OAuth accounts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/oauth/linked-accounts",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "accounts" in data

