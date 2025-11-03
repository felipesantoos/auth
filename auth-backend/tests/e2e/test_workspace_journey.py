"""E2E tests for workspace journey"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestWorkspaceJourney:
    """End-to-end tests for complete workspace workflows"""
    
    async def test_register_user_creates_workspace(
        self, 
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test complete journey: register user → workspace created automatically
        """
        # 1. Register a new user with custom workspace name
        register_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "Test1234!@#$",
            "name": "Test User",
            "workspace_name": "My Custom Workspace"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        
        # Registration should succeed
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["email"] == "testuser@example.com"
        assert user_data["username"] == "testuser"
        
        # Note: We would need to verify workspace creation here,
        # but that requires authentication and workspace endpoints
        # This is a basic e2e test to ensure registration works
    
    async def test_workspace_crud_journey(
        self,
        client: AsyncClient,
        authenticated_client: AsyncClient
    ):
        """
        Test complete CRUD journey for workspaces
        (Requires authenticated client fixture)
        """
        # 1. Create a workspace
        workspace_data = {
            "name": "Test Company",
            "slug": "test-company",
            "description": "A test company workspace"
        }
        
        create_response = await authenticated_client.post(
            "/api/v1/workspaces",
            json=workspace_data
        )
        
        # Should create successfully
        assert create_response.status_code == 201
        created = create_response.json()
        workspace_id = created["id"]
        assert created["name"] == "Test Company"
        assert created["slug"] == "test-company"
        
        # 2. Get the workspace
        get_response = await authenticated_client.get(
            f"/api/v1/workspaces/{workspace_id}"
        )
        
        assert get_response.status_code == 200
        workspace = get_response.json()
        assert workspace["id"] == workspace_id
        assert workspace["name"] == "Test Company"
        
        # 3. Update the workspace
        update_data = {
            "name": "Updated Company Name",
            "description": "Updated description"
        }
        
        update_response = await authenticated_client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json=update_data
        )
        
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Updated Company Name"
        assert updated["description"] == "Updated description"
        
        # 4. List workspaces (should include our workspace)
        list_response = await authenticated_client.get("/api/v1/workspaces")
        
        assert list_response.status_code == 200
        workspaces_list = list_response.json()
        assert workspaces_list["total"] >= 1
        
        # 5. Delete the workspace
        delete_response = await authenticated_client.delete(
            f"/api/v1/workspaces/{workspace_id}"
        )
        
        assert delete_response.status_code == 204
        
        # 6. Verify deletion
        get_deleted = await authenticated_client.get(
            f"/api/v1/workspaces/{workspace_id}"
        )
        
        assert get_deleted.status_code == 404

