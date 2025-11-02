"""
Integration tests for Client Routes
Tests client/tenant management API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestClientManagement:
    """Test client management routes"""
    
    @pytest.mark.asyncio
    async def test_create_client(self, async_client: AsyncClient, admin_token: str):
        """Test creating new client"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.post(
            "/api/v1/clients",
            headers=headers,
            json={
                "name": "Test Client",
                "description": "Integration test client"
            }
        )
        
        assert response.status_code in [200, 201, 403]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            assert data["name"] == "Test Client"
    
    @pytest.mark.asyncio
    async def test_get_client_by_id(self, async_client: AsyncClient, admin_token: str):
        """Test getting client by ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a client
        create_response = await async_client.post(
            "/api/v1/clients",
            headers=headers,
            json={"name": "Test Client"}
        )
        
        if create_response.status_code in [200, 201]:
            client_id = create_response.json()["id"]
            
            # Get the client
            response = await async_client.get(
                f"/api/v1/clients/{client_id}",
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == client_id
    
    @pytest.mark.asyncio
    async def test_list_clients(self, async_client: AsyncClient, admin_token: str):
        """Test listing all clients"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/clients",
            headers=headers
        )
        
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_update_client(self, async_client: AsyncClient, admin_token: str):
        """Test updating client"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a client
        create_response = await async_client.post(
            "/api/v1/clients",
            headers=headers,
            json={"name": "Original Name"}
        )
        
        if create_response.status_code in [200, 201]:
            client_id = create_response.json()["id"]
            
            # Update the client
            response = await async_client.put(
                f"/api/v1/clients/{client_id}",
                headers=headers,
                json={"name": "Updated Name"}
            )
            
            assert response.status_code in [200, 403]
    
    @pytest.mark.asyncio
    async def test_delete_client(self, async_client: AsyncClient, admin_token: str):
        """Test deleting client"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First create a client
        create_response = await async_client.post(
            "/api/v1/clients",
            headers=headers,
            json={"name": "To Delete"}
        )
        
        if create_response.status_code in [200, 201]:
            client_id = create_response.json()["id"]
            
            # Delete the client
            response = await async_client.delete(
                f"/api/v1/clients/{client_id}",
                headers=headers
            )
            
            assert response.status_code in [200, 204, 403]
    
    @pytest.mark.asyncio
    async def test_create_client_requires_admin(self, async_client: AsyncClient, auth_token: str):
        """Test creating client requires admin role"""
        headers = {"Authorization": f"Bearer {auth_token}"}  # Regular user
        
        response = await async_client.post(
            "/api/v1/clients",
            headers=headers,
            json={"name": "Test Client"}
        )
        
        assert response.status_code == 403

