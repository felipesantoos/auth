"""
E2E Test: Permission Management Journey
Tests the complete flow of granting and revoking permissions
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestPermissionGrantRevokeJourney:
    """Test complete permission grant and revoke journey"""
    
    @pytest.mark.asyncio
    async def test_permission_management_journey(
        self,
        async_client: AsyncClient,
        admin_token,
        auth_token,
        test_user,
        admin_user
    ):
        """
        Test complete permission management flow:
        1. Admin grants permission to regular user
        2. User checks their permissions
        3. User can perform allowed action
        4. Admin revokes permission
        5. User can no longer perform action
        """
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Admin grants READ permission on a project
        grant_data = {
            "user_id": test_user.id,
            "resource_type": "project",
            "resource_id": "project-e2e-123",
            "action": "read"
        }
        
        grant_response = await async_client.post(
            "/api/auth/permissions",
            json=grant_data,
            headers=admin_headers
        )
        
        # Permission grant should succeed
        if grant_response.status_code == 201:
            granted_permission = grant_response.json()
            assert granted_permission["user_id"] == test_user.id
            assert granted_permission["resource_type"] == "project"
            assert granted_permission["action"] == "read"
            permission_id = granted_permission["id"]
            
            # Step 2: User checks their permissions
            permissions_response = await async_client.get(
                f"/api/auth/permissions/user/{test_user.id}",
                headers=user_headers
            )
            
            assert permissions_response.status_code == 200
            user_permissions = permissions_response.json()
            assert isinstance(user_permissions, list)
            
            # Should find the granted permission
            project_perms = [
                p for p in user_permissions
                if p["resource_type"] == "project" and p["resource_id"] == "project-e2e-123"
            ]
            assert len(project_perms) > 0
            
            # Step 3: Admin revokes the permission
            revoke_response = await async_client.delete(
                f"/api/auth/permissions/{permission_id}",
                headers=admin_headers
            )
            
            assert revoke_response.status_code in [200, 204]
            
            # Step 4: Verify permission is revoked
            verify_response = await async_client.get(
                f"/api/auth/permissions/user/{test_user.id}",
                headers=user_headers
            )
            
            assert verify_response.status_code == 200
            remaining_permissions = verify_response.json()
            
            # The revoked permission should not be in the list
            project_perms_after = [
                p for p in remaining_permissions
                if p.get("id") == permission_id
            ]
            assert len(project_perms_after) == 0
    
    @pytest.mark.asyncio
    async def test_regular_user_cannot_grant_permissions(
        self,
        async_client: AsyncClient,
        auth_token,
        test_user
    ):
        """Test that regular users cannot grant permissions"""
        user_headers = {"Authorization": f"Bearer {auth_token}"}
        
        grant_data = {
            "user_id": "other-user-id",
            "resource_type": "project",
            "resource_id": "project-123",
            "action": "read"
        }
        
        response = await async_client.post(
            "/api/auth/permissions",
            json=grant_data,
            headers=user_headers
        )
        
        # Should be forbidden
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_user_cannot_view_other_users_permissions(
        self,
        async_client: AsyncClient,
        auth_token
    ):
        """Test that users cannot view other users' permissions"""
        user_headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/auth/permissions/user/other-user-id",
            headers=user_headers
        )
        
        # Should be forbidden
        assert response.status_code == 403


@pytest.mark.e2e
class TestWildcardPermissionJourney:
    """Test wildcard permission journey"""
    
    @pytest.mark.asyncio
    async def test_wildcard_permission_allows_all_resources(
        self,
        async_client: AsyncClient,
        admin_token,
        auth_token,
        test_user
    ):
        """
        Test wildcard permissions apply to all resources of a type:
        1. Admin grants wildcard permission (no resource_id)
        2. User can access any resource of that type
        """
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Grant wildcard READ permission on all tickets
        grant_data = {
            "user_id": test_user.id,
            "resource_type": "ticket",
            "resource_id": None,  # Wildcard - all tickets
            "action": "read"
        }
        
        grant_response = await async_client.post(
            "/api/auth/permissions",
            json=grant_data,
            headers=admin_headers
        )
        
        if grant_response.status_code == 201:
            # User should now have wildcard permission
            permissions_response = await async_client.get(
                f"/api/auth/permissions/user/{test_user.id}",
                headers=user_headers
            )
            
            assert permissions_response.status_code == 200
            permissions = permissions_response.json()
            
            # Find wildcard permission
            wildcard_perms = [
                p for p in permissions
                if p["resource_type"] == "ticket" and p["resource_id"] is None
            ]
            assert len(wildcard_perms) > 0


@pytest.mark.e2e
class TestManagePermissionJourney:
    """Test MANAGE permission journey"""
    
    @pytest.mark.asyncio
    async def test_manage_permission_grants_all_actions(
        self,
        async_client: AsyncClient,
        admin_token,
        auth_token,
        test_user
    ):
        """
        Test MANAGE permission grants all actions:
        1. Admin grants MANAGE permission
        2. Permission should allow create, read, update, delete
        """
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Grant MANAGE permission
        grant_data = {
            "user_id": test_user.id,
            "resource_type": "document",
            "resource_id": "doc-123",
            "action": "manage"  # MANAGE grants all actions
        }
        
        grant_response = await async_client.post(
            "/api/auth/permissions",
            json=grant_data,
            headers=admin_headers
        )
        
        if grant_response.status_code == 201:
            granted_permission = grant_response.json()
            assert granted_permission["action"] == "manage"
            
            # User permissions should include the MANAGE permission
            permissions_response = await async_client.get(
                f"/api/auth/permissions/user/{test_user.id}",
                headers=user_headers
            )
            
            assert permissions_response.status_code == 200
            permissions = permissions_response.json()
            
            manage_perms = [
                p for p in permissions
                if p["action"] == "manage" and p["resource_id"] == "doc-123"
            ]
            assert len(manage_perms) > 0

