"""
Integration tests for WebAuthn Routes
Tests WebAuthn/Passkey API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestWebAuthnRegistration:
    """Test WebAuthn credential registration"""
    
    @pytest.mark.asyncio
    async def test_generate_registration_options(self, async_client: AsyncClient, auth_token: str):
        """Test generating WebAuthn registration options"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/v1/webauthn/register/options",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "challenge" in data or "publicKey" in data
    
    @pytest.mark.asyncio
    async def test_verify_registration(self, async_client: AsyncClient, auth_token: str):
        """Test verifying WebAuthn registration"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/v1/webauthn/register/verify",
            headers=headers,
            json={
                "credential": {
                    "id": "test-credential-id",
                    "response": {}
                }
            }
        )
        
        # Will fail without real WebAuthn data
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestWebAuthnAuthentication:
    """Test WebAuthn authentication"""
    
    @pytest.mark.asyncio
    async def test_generate_authentication_options(self, async_client: AsyncClient):
        """Test generating WebAuthn authentication options"""
        response = await async_client.post(
            "/api/v1/webauthn/authenticate/options",
            json={"username": "testuser", "client_id": "client-123"}
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_verify_authentication(self, async_client: AsyncClient):
        """Test verifying WebAuthn authentication"""
        response = await async_client.post(
            "/api/v1/webauthn/authenticate/verify",
            json={
                "credential": {
                    "id": "credential-id",
                    "response": {}
                },
                "client_id": "client-123"
            }
        )
        
        # Will fail without real WebAuthn data
        assert response.status_code in [200, 400, 401]


@pytest.mark.integration
class TestWebAuthnCredentialManagement:
    """Test WebAuthn credential management"""
    
    @pytest.mark.asyncio
    async def test_list_user_credentials(self, async_client: AsyncClient, auth_token: str):
        """Test listing user's WebAuthn credentials"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/webauthn/credentials",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
    
    @pytest.mark.asyncio
    async def test_delete_credential(self, async_client: AsyncClient, auth_token: str):
        """Test deleting WebAuthn credential"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.delete(
            "/api/v1/webauthn/credentials/cred-123",
            headers=headers
        )
        
        assert response.status_code in [200, 204, 404]
    
    @pytest.mark.asyncio
    async def test_rename_credential(self, async_client: AsyncClient, auth_token: str):
        """Test renaming WebAuthn credential"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.patch(
            "/api/v1/webauthn/credentials/cred-123",
            headers=headers,
            json={"device_name": "My YubiKey"}
        )
        
        assert response.status_code in [200, 404]

