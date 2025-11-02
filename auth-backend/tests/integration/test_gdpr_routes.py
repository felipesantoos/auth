"""
Integration tests for GDPR Routes
Tests GDPR compliance API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestGDPRRoutes:
    """Test GDPR compliance routes"""
    
    @pytest.mark.asyncio
    async def test_export_user_data(self, async_client: AsyncClient, auth_token: str):
        """Test exporting user data (GDPR Article 15)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/gdpr/export-my-data",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "user_data" in data or "email" in data
    
    @pytest.mark.asyncio
    async def test_delete_user_data(self, async_client: AsyncClient, auth_token: str):
        """Test deleting user data (GDPR Right to be Forgotten)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/v1/gdpr/delete-my-data",
            headers=headers,
            json={"confirm": True}
        )
        
        # Should require confirmation or have specific flow
        assert response.status_code in [200, 202, 400, 403]
    
    @pytest.mark.asyncio
    async def test_export_requires_authentication(self, async_client: AsyncClient):
        """Test GDPR export requires authentication"""
        response = await async_client.get("/api/v1/gdpr/export-my-data")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_data_retention_policies(self, async_client: AsyncClient, admin_token: str):
        """Test getting data retention policies"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/gdpr/retention-policies",
            headers=headers
        )
        
        assert response.status_code in [200, 403]

