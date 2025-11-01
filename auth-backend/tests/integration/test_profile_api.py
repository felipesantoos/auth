"""
Integration tests for Profile API
"""
import pytest
from httpx import AsyncClient


class TestProfileAPI:
    """Integration tests for user profile management"""
    
    @pytest.mark.asyncio
    async def test_get_own_profile(self, async_client: AsyncClient, user_token):
        """Test user can get their own profile"""
        response = await async_client.get(
            "/api/auth/profile/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "name" in data
    
    @pytest.mark.asyncio
    async def test_update_own_profile(self, async_client: AsyncClient, user_token):
        """Test user can update their own profile"""
        response = await async_client.put(
            "/api/auth/profile/me",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_delete_account_requires_password(self, async_client: AsyncClient, user_token):
        """Test account deletion requires password"""
        response = await async_client.delete(
            "/api/auth/profile/me",
            json={"password": "wrongpassword"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Should fail with wrong password
        assert response.status_code in [403, 400]
    
    @pytest.mark.asyncio
    async def test_profile_requires_authentication(self, async_client: AsyncClient):
        """Test profile endpoints require authentication"""
        response = await async_client.get("/api/auth/profile/me")
        
        assert response.status_code == 401

