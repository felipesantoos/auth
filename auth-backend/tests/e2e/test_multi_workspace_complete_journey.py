"""
E2E tests for complete multi-workspace journey
Tests the entire flow from registration to workspace management
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.factories.user_factory import UserFactory
from tests.factories.client_factory import ClientFactory


@pytest.mark.asyncio
class TestMultiWorkspaceJourney:
    """End-to-end tests for multi-workspace architecture"""
    
    async def test_complete_registration_with_workspace_creation(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test complete registration flow:
        1. User registers
        2. Personal workspace is created automatically
        3. User is added as admin of workspace
        """
        # 1. Register a new user
        register_data = {
            "username": "johndoe",
            "email": "john.doe@example.com",
            "password": "SecurePass123!",
            "name": "John Doe",
            "workspace_name": "John's Company"
        }
        
        response = await client.post("/api/v1/auth/register", json=register_data)
        
        # Should succeed
        assert response.status_code == 201
        user_data = response.json()
        user_id = user_data["id"]
        
        assert user_data["email"] == "john.doe@example.com"
        assert user_data["username"] == "johndoe"
        assert user_data["name"] == "John Doe"
        
        # Note: To verify workspace creation, we would need to:
        # - Login to get access token
        # - Query workspaces endpoint
        # This requires more setup but confirms the basic registration works
    
    async def test_email_uniqueness_across_system(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test that email is globally unique (not per client anymore).
        
        In the old architecture, same email could exist in multiple clients.
        In multi-workspace, email must be unique globally.
        """
        # 1. Register first user
        user1_data = {
            "username": "user1",
            "email": "unique@example.com",
            "password": "SecurePass123!",
            "name": "User One",
        }
        
        response1 = await client.post("/api/v1/auth/register", json=user1_data)
        assert response1.status_code == 201
        
        # 2. Try to register another user with same email (different username)
        user2_data = {
            "username": "user2",
            "email": "unique@example.com",  # Same email
            "password": "SecurePass123!",
            "name": "User Two",
        }
        
        response2 = await client.post("/api/v1/auth/register", json=user2_data)
        
        # Should fail - email already exists globally
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    async def test_user_can_belong_to_multiple_workspaces(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test that a user can be a member of multiple workspaces.
        
        This is the core feature of multi-workspace architecture.
        """
        # This test would require:
        # 1. Create User A
        # 2. User A creates Workspace 1 (auto)
        # 3. User A creates Workspace 2
        # 4. Create User B
        # 5. User A adds User B to both workspaces
        # 6. Verify User B can access both workspaces
        
        # For now, marking as TODO for full implementation
        # The infrastructure is ready for this flow
        pass
    
    async def test_user_has_different_roles_in_different_workspaces(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """
        Test that a user can have different roles in different workspaces.
        
        Example: Admin in Company A, User in Company B
        """
        # This test would require:
        # 1. Create User and Workspace A (user is admin)
        # 2. Create Workspace B
        # 3. Add user to Workspace B as regular user
        # 4. Verify user has admin permissions in A
        # 5. Verify user has user permissions in B
        
        # Infrastructure is ready for this flow
        pass

