"""
Integration tests for Passwordless Routes
Tests magic link authentication API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestPasswordlessEndpoints:
    """Test passwordless authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_request_magic_link_endpoint_exists(self, async_client: AsyncClient):
        """Test request magic link endpoint exists"""
        response = await async_client.post(
            "/api/auth/passwordless/request",
            json={"email": "test@example.com"}
        )
        
        # Endpoint should exist
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_request_magic_link_with_invalid_email(self, async_client: AsyncClient):
        """Test requesting magic link with invalid email"""
        response = await async_client.post(
            "/api/auth/passwordless/request",
            json={"email": "invalid-email"}
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_verify_magic_link_endpoint_exists(self, async_client: AsyncClient):
        """Test verify magic link endpoint exists"""
        response = await async_client.post(
            "/api/auth/passwordless/verify",
            json={"email": "test@example.com", "token": "test-token"}
        )
        
        # Endpoint should exist
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_verify_magic_link_with_invalid_token(self, async_client: AsyncClient):
        """Test verifying with invalid magic link token"""
        response = await async_client.post(
            "/api/auth/passwordless/verify",
            json={"email": "test@example.com", "token": "invalid-token"}
        )
        
        # Should fail
        assert response.status_code in [400, 401, 422]

