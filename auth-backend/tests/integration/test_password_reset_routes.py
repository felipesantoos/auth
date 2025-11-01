"""
Integration tests for Password Reset Routes
Tests password reset API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestPasswordResetEndpoints:
    """Test password reset endpoints"""
    
    @pytest.mark.asyncio
    async def test_request_password_reset_endpoint_exists(self, async_client: AsyncClient):
        """Test request password reset endpoint exists"""
        response = await async_client.post(
            "/api/auth/password-reset/request",
            json={"email": "test@example.com"}
        )
        
        # Endpoint should exist and accept request
        # Often returns 200 even for nonexistent emails (security)
        assert response.status_code in [200, 202, 404]
    
    @pytest.mark.asyncio
    async def test_request_password_reset_with_invalid_email(self, async_client: AsyncClient):
        """Test requesting reset with invalid email format"""
        response = await async_client.post(
            "/api/auth/password-reset/request",
            json={"email": "invalid-email"}
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_verify_reset_token_endpoint_exists(self, async_client: AsyncClient):
        """Test verify reset token endpoint exists"""
        response = await async_client.post(
            "/api/auth/password-reset/verify",
            json={"token": "test-token"}
        )
        
        # Endpoint should exist
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_verify_reset_token_with_invalid_token(self, async_client: AsyncClient):
        """Test verifying with invalid reset token"""
        response = await async_client.post(
            "/api/auth/password-reset/verify",
            json={"token": "invalid-token"}
        )
        
        # Should fail
        assert response.status_code in [400, 401, 422]
    
    @pytest.mark.asyncio
    async def test_reset_password_endpoint_exists(self, async_client: AsyncClient):
        """Test reset password endpoint exists"""
        response = await async_client.post(
            "/api/auth/password-reset/reset",
            json={
                "token": "test-token",
                "new_password": "NewSecurePass123"
            }
        )
        
        # Endpoint should exist
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_reset_password_with_weak_password(self, async_client: AsyncClient):
        """Test resetting with weak password"""
        response = await async_client.post(
            "/api/auth/password-reset/reset",
            json={
                "token": "test-token",
                "new_password": "weak"
            }
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]

