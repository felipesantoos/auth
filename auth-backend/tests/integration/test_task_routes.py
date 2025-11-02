"""
Integration tests for Task Routes
Tests async task API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestTaskRoutes:
    """Test async task routes"""
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, async_client: AsyncClient, auth_token: str):
        """Test getting task status by ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/tasks/task-123",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_list_user_tasks(self, async_client: AsyncClient, auth_token: str):
        """Test listing user's tasks"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/tasks",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, async_client: AsyncClient, auth_token: str):
        """Test cancelling a task"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/v1/tasks/task-123/cancel",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_tasks_require_authentication(self, async_client: AsyncClient):
        """Test task endpoints require authentication"""
        response = await async_client.get("/api/v1/tasks")
        
        assert response.status_code == 401

