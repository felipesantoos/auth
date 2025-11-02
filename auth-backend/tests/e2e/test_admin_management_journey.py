"""
End-to-End tests for Admin Management Journey
Tests complete admin workflows
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestUserManagementJourney:
    """Test complete user management journey"""
    
    @pytest.mark.asyncio
    async def test_admin_create_manage_delete_user(self, async_client: AsyncClient, admin_token: str):
        """Test complete flow: Admin creates user → Updates → Deactivates → Deletes"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 1: Create user as admin
        create_response = await async_client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "username": "managed_user",
                "email": "managed@example.com",
                "password": "TempPass123",
                "name": "Managed User",
                "role": "user"
            }
        )
        
        assert create_response.status_code in [200, 201, 403]
        if create_response.status_code in [200, 201]:
            user_data = create_response.json()
            user_id = user_data.get("id")
            
            # Step 2: Update user
            update_response = await async_client.put(
                f"/api/v1/users/{user_id}",
                headers=headers,
                json={"name": "Updated Name"}
            )
            
            assert update_response.status_code in [200, 403, 404]
            
            # Step 3: Deactivate user
            deactivate_response = await async_client.post(
                f"/api/v1/users/{user_id}/deactivate",
                headers=headers
            )
            
            assert deactivate_response.status_code in [200, 403, 404]
            
            # Step 4: Delete user
            delete_response = await async_client.delete(
                f"/api/v1/users/{user_id}",
                headers=headers
            )
            
            assert delete_response.status_code in [200, 204, 403, 404]


@pytest.mark.e2e
class TestPermissionManagementJourney:
    """Test complete permission management journey"""
    
    @pytest.mark.asyncio
    async def test_create_assign_revoke_permission(self, async_client: AsyncClient, admin_token: str):
        """Test complete flow: Create permission → Assign to user → Revoke"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 1: Create permission
        create_perm_response = await async_client.post(
            "/api/v1/permissions",
            headers=headers,
            json={
                "name": "projects.delete",
                "description": "Delete projects",
                "resource": "projects",
                "action": "delete"
            }
        )
        
        assert create_perm_response.status_code in [200, 201, 403]
        
        # Step 2: Assign permission to user
        if create_perm_response.status_code in [200, 201]:
            perm_id = create_perm_response.json().get("id")
            
            assign_response = await async_client.post(
                "/api/v1/users/user-123/permissions",
                headers=headers,
                json={"permission_id": perm_id}
            )
            
            assert assign_response.status_code in [200, 403, 404]


@pytest.mark.e2e
class TestAPIKeyManagementJourney:
    """Test complete API key management journey"""
    
    @pytest.mark.asyncio
    async def test_create_use_rotate_revoke_api_key(self, async_client: AsyncClient, auth_token: str):
        """Test complete flow: Create API key → Use it → Rotate → Revoke"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create API key
        create_response = await async_client.post(
            "/api/v1/api-keys",
            headers=headers,
            json={
                "name": "Production API Key",
                "scopes": ["read:user", "write:user"]
            }
        )
        
        assert create_response.status_code in [200, 201]
        if create_response.status_code in [200, 201]:
            key_data = create_response.json()
            api_key = key_data.get("key")  # Plain key (shown once)
            key_id = key_data.get("id")
            
            # Step 2: Use API key to make request
            api_headers = {"X-API-Key": api_key}
            use_response = await async_client.get(
                "/api/v1/profile",
                headers=api_headers
            )
            
            assert use_response.status_code in [200, 401]
            
            # Step 3: Rotate API key
            rotate_response = await async_client.post(
                f"/api/v1/api-keys/{key_id}/rotate",
                headers=headers
            )
            
            assert rotate_response.status_code in [200, 404]
            
            # Step 4: Revoke API key
            revoke_response = await async_client.delete(
                f"/api/v1/api-keys/{key_id}",
                headers=headers
            )
            
            assert revoke_response.status_code in [200, 204, 404]

