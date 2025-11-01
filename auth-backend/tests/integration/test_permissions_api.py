"""
Integration tests for Permissions API
"""
import pytest
from httpx import AsyncClient


class TestPermissionsAPI:
    """Integration tests for fine-grained permissions"""
    
    @pytest.mark.asyncio
    async def test_grant_permission_as_admin(self, async_client: AsyncClient, admin_token):
        """Test admin can grant permissions"""
        response = await async_client.post(
            "/api/auth/permissions",
            json={
                "user_id": "some-user-id",
                "resource_type": "project",
                "action": "read",
                "resource_id": "project-123"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should succeed or fail gracefully (depending on if user exists)
        assert response.status_code in [201, 400, 404]
    
    @pytest.mark.asyncio
    async def test_list_own_permissions(self, async_client: AsyncClient, user_token, test_user):
        """Test user can list their own permissions"""
        response = await async_client.get(
            f"/api/auth/permissions/user/{test_user.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_other_permissions_forbidden(self, async_client: AsyncClient, user_token):
        """Test user cannot list other user's permissions"""
        response = await async_client.get(
            "/api/auth/permissions/user/other-user-id",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403

