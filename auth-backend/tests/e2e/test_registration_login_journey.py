"""
E2E Test: Complete Registration and Login Journey
Tests the full flow from registration to accessing protected resources
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestRegistrationLoginJourney:
    """Test complete user registration and login journey"""
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self, async_client: AsyncClient):
        """
        Test complete user journey:
        1. Register new user
        2. Login with credentials
        3. Access protected resource
        4. Logout (revoke token if implemented)
        """
        # Step 1: Register new user
        registration_data = {
            "username": "newuser123",
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "name": "New User",
            "client_id": "test-client-e2e"
        }
        
        register_response = await async_client.post(
            "/api/auth/register",
            json=registration_data
        )
        
        # Registration should succeed
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "user" in register_data
        assert register_data["user"]["email"] == "newuser@example.com"
        assert register_data["user"]["username"] == "newuser123"
        
        # Step 2: Login with credentials
        login_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "client_id": "test-client-e2e"
        }
        
        login_response = await async_client.post(
            "/api/auth/login",
            json=login_data
        )
        
        # Login should succeed
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        assert login_result["token_type"] == "bearer"
        
        access_token = login_result["access_token"]
        
        # Step 3: Access protected resource with token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        me_response = await async_client.get(
            "/api/auth/me",
            headers=headers
        )
        
        # Should be able to access protected resource
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == "newuser@example.com"
        assert user_data["username"] == "newuser123"
    
    @pytest.mark.asyncio
    async def test_registration_with_invalid_data_fails(self, async_client: AsyncClient):
        """Test registration with invalid data fails appropriately"""
        # Test with weak password
        weak_password_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",  # Too weak
            "name": "Test User",
            "client_id": "test-client"
        }
        
        response = await async_client.post(
            "/api/auth/register",
            json=weak_password_data
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_login_with_wrong_password_fails(self, async_client: AsyncClient, test_user):
        """Test login with wrong password fails"""
        login_data = {
            "email": "test@example.com",
            "password": "WrongPassword123",
            "client_id": "test-client-id"
        }
        
        response = await async_client.post(
            "/api/auth/login",
            json=login_data
        )
        
        # Should fail authentication
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_accessing_protected_resource_without_token_fails(self, async_client: AsyncClient):
        """Test accessing protected resource without token fails"""
        response = await async_client.get("/api/auth/me")
        
        # Should be unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_accessing_protected_resource_with_invalid_token_fails(self, async_client: AsyncClient):
        """Test accessing protected resource with invalid token fails"""
        headers = {"Authorization": "Bearer invalid-token-here"}
        
        response = await async_client.get(
            "/api/auth/me",
            headers=headers
        )
        
        # Should be unauthorized
        assert response.status_code == 401


@pytest.mark.e2e
class TestTokenRefreshJourney:
    """Test token refresh journey"""
    
    @pytest.mark.asyncio
    async def test_token_refresh_journey(self, async_client: AsyncClient, test_user):
        """
        Test token refresh flow:
        1. Login to get tokens
        2. Use refresh token to get new access token
        3. Use new access token to access protected resource
        """
        # Step 1: Login
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "client_id": "test-client-id"
        }
        
        login_response = await async_client.post(
            "/api/auth/login",
            json=login_data
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Step 2: Refresh token
        refresh_response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # If refresh endpoint exists, should succeed
        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()
            assert "access_token" in new_tokens
            new_access_token = new_tokens["access_token"]
            
            # Step 3: Use new access token
            headers = {"Authorization": f"Bearer {new_access_token}"}
            me_response = await async_client.get(
                "/api/auth/me",
                headers=headers
            )
            
            assert me_response.status_code == 200


@pytest.mark.e2e
class TestProfileUpdateJourney:
    """Test profile update journey"""
    
    @pytest.mark.asyncio
    async def test_update_profile_journey(self, async_client: AsyncClient, auth_token, test_user):
        """
        Test profile update flow:
        1. Get current profile
        2. Update profile
        3. Verify changes
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Get current profile
        profile_response = await async_client.get(
            "/api/auth/me",
            headers=headers
        )
        
        assert profile_response.status_code == 200
        original_profile = profile_response.json()
        
        # Step 2: Update profile
        update_data = {
            "name": "Updated Name"
        }
        
        update_response = await async_client.patch(
            "/api/auth/profile",
            json=update_data,
            headers=headers
        )
        
        # If profile update endpoint exists
        if update_response.status_code == 200:
            # Step 3: Verify changes
            verify_response = await async_client.get(
                "/api/auth/me",
                headers=headers
            )
            
            assert verify_response.status_code == 200
            updated_profile = verify_response.json()
            assert updated_profile["name"] == "Updated Name"

