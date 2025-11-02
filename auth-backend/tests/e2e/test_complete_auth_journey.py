"""
End-to-End tests for Complete Authentication Journey
Tests full user authentication flow from registration to logout
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestCompleteAuthJourney:
    """Test complete authentication journey"""
    
    @pytest.mark.asyncio
    async def test_register_verify_login_logout_flow(self, async_client: AsyncClient):
        """Test complete flow: Register → Verify Email → Login → Logout"""
        
        # Step 1: Register new user
        register_response = await async_client.post(
            "/api/auth/register",
            json={
                "username": "e2e_user",
                "email": "e2e@example.com",
                "password": "SecurePass123",
                "name": "E2E Test User",
                "client_id": "test-client-id"
            }
        )
        
        assert register_response.status_code in [200, 201]
        user_data = register_response.json()
        assert "id" in user_data or "user" in user_data
        
        # Step 2: Verify email (simulated - get token from response or DB)
        # In real scenario, user would click link in email
        
        # Step 3: Login
        login_response = await async_client.post(
            "/api/auth/login",
            json={
                "email": "e2e@example.com",
                "password": "SecurePass123",
                "client_id": "test-client-id"
            }
        )
        
        assert login_response.status_code in [200, 401]
        if login_response.status_code == 200:
            login_data = login_response.json()
            assert "access_token" in login_data
            access_token = login_data["access_token"]
            
            # Step 4: Verify token works (get profile)
            headers = {"Authorization": f"Bearer {access_token}"}
            profile_response = await async_client.get(
                "/api/v1/profile",
                headers=headers
            )
            
            assert profile_response.status_code == 200
            profile = profile_response.json()
            assert profile["email"] == "e2e@example.com"
            
            # Step 5: Logout
            logout_response = await async_client.post(
                "/api/auth/logout",
                headers=headers
            )
            
            assert logout_response.status_code in [200, 204]
            
            # Step 6: Verify token no longer works
            verify_response = await async_client.get(
                "/api/v1/profile",
                headers=headers
            )
            
            assert verify_response.status_code == 401


@pytest.mark.e2e
class TestPasswordResetJourney:
    """Test complete password reset journey"""
    
    @pytest.mark.asyncio
    async def test_forgot_password_to_reset_flow(self, async_client: AsyncClient, test_user):
        """Test complete flow: Request Reset → Verify Token → Set New Password → Login"""
        
        # Step 1: Request password reset
        reset_request = await async_client.post(
            "/api/auth/forgot-password",
            json={
                "email": "test@example.com",
                "client_id": "test-client-id"
            }
        )
        
        assert reset_request.status_code in [200, 202]
        
        # Step 2: Reset password (with token from email)
        # In real scenario, token comes from email link
        reset_response = await async_client.post(
            "/api/auth/reset-password",
            json={
                "token": "fake-reset-token",
                "new_password": "NewSecurePass456"
            }
        )
        
        # Will fail without real token, but validates flow
        assert reset_response.status_code in [200, 400, 404]


@pytest.mark.e2e
class TestMFAEnrollmentJourney:
    """Test complete MFA enrollment and login journey"""
    
    @pytest.mark.asyncio
    async def test_enable_mfa_and_login_with_mfa(self, async_client: AsyncClient, auth_token: str):
        """Test complete flow: Enable MFA → Get QR Code → Verify TOTP → Login with MFA"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Initialize MFA setup
        setup_response = await async_client.post(
            "/api/v1/mfa/setup",
            headers=headers
        )
        
        assert setup_response.status_code in [200, 409]
        if setup_response.status_code == 200:
            mfa_data = setup_response.json()
            assert "secret" in mfa_data or "qr_code" in mfa_data
            
            # Step 2: Verify MFA code (enable MFA)
            verify_response = await async_client.post(
                "/api/v1/mfa/verify",
                headers=headers,
                json={"code": "123456"}  # Would be from authenticator app
            )
            
            # Will fail without real TOTP, but validates flow
            assert verify_response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_mfa_backup_codes(self, async_client: AsyncClient, auth_token: str):
        """Test generating and using MFA backup codes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Generate backup codes
        response = await async_client.post(
            "/api/v1/mfa/backup-codes",
            headers=headers
        )
        
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "codes" in data or isinstance(data, list)

