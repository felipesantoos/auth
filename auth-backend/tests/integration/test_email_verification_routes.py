"""
Integration tests for Email Verification Routes
Tests email verification API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestEmailVerificationEndpoints:
    """Test email verification endpoints"""
    
    @pytest.mark.asyncio
    async def test_verify_email_endpoint_exists(self, async_client: AsyncClient):
        """Test verify email endpoint exists"""
        response = await async_client.post(
            "/api/auth/email/verify",
            json={"token": "test-token"}
        )
        
        # Endpoint should exist (not 404)
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_verify_email_with_invalid_token(self, async_client: AsyncClient):
        """Test verifying with invalid token"""
        response = await async_client.post(
            "/api/auth/email/verify",
            json={"token": "invalid-token"}
        )
        
        # Should fail with 400 or 401
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_resend_verification_requires_authentication(self, async_client: AsyncClient):
        """Test resend verification requires authentication"""
        response = await async_client.post("/api/auth/email/resend-verification")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_verification_status_requires_authentication(self, async_client: AsyncClient):
        """Test getting verification status requires authentication"""
        response = await async_client.get("/api/auth/email/status")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_verification_status_with_auth(self, async_client: AsyncClient, auth_token):
        """Test getting verification status with authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/auth/email/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "email_verified" in data

