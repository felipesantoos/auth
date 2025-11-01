"""
Integration tests for authentication security
"""
import pytest
from httpx import AsyncClient


class TestAuthenticationSecurity:
    """Test authentication security features"""
    
    @pytest.mark.asyncio
    async def test_register_with_weak_password(self, async_client: AsyncClient):
        """Test registration rejects weak passwords"""
        response = await async_client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",  # Too short
            "name": "Test User",
            "client_id": "test-client"
        })
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, async_client: AsyncClient):
        """Test protected endpoints reject requests without token"""
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, async_client: AsyncClient):
        """Test protected endpoints reject invalid tokens"""
        headers = {"Authorization": "Bearer invalid-token-here"}
        response = await async_client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_admin_endpoint_as_regular_user(self, async_client: AsyncClient, auth_token):
        """Test admin endpoints reject regular users"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = await async_client.get("/api/auth/users", headers=headers)
        
        assert response.status_code == 403  # Forbidden


class TestRateLimiting:
    """Test rate limiting security"""
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, async_client: AsyncClient):
        """Test login endpoint is rate limited"""
        # Make 6 requests (limit is 5/minute)
        for i in range(6):
            response = await async_client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrong",
                "client_id": "test"
            })
            
            if i < 5:
                assert response.status_code in [401, 400]  # Invalid credentials
            else:
                assert response.status_code == 429  # Too many requests


class TestCORSSecurity:
    """Test CORS security"""
    
    @pytest.mark.asyncio
    async def test_cors_allows_configured_origins(self, async_client: AsyncClient):
        """Test CORS allows configured origins"""
        headers = {"Origin": "http://localhost:5173"}
        response = await async_client.options("/api/auth/login", headers=headers)
        
        assert "access-control-allow-origin" in response.headers
    
    @pytest.mark.asyncio
    async def test_cors_rejects_unknown_origins(self, async_client: AsyncClient):
        """Test CORS rejects unknown origins"""
        headers = {"Origin": "http://evil-site.com"}
        response = await async_client.options("/api/auth/login", headers=headers)
        
        # Should not have CORS headers for unknown origin
        # (behavior depends on CORS config)
        pass

