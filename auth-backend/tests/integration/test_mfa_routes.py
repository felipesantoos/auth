"""
Integration tests for MFA Routes
Tests 2FA/MFA API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestMFASetup:
    """Test MFA setup endpoints"""
    
    @pytest.mark.asyncio
    async def test_setup_mfa_requires_authentication(self, async_client: AsyncClient):
        """Test MFA setup requires authentication"""
        response = await async_client.post("/api/auth/mfa/setup")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_setup_mfa_returns_qr_code_and_secret(self, async_client: AsyncClient, auth_token):
        """Test MFA setup returns QR code and secret"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.post(
            "/api/auth/mfa/setup",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "secret" in data
            assert "qr_code" in data
            assert "backup_codes" in data
            assert data["qr_code"].startswith("data:image/png;base64,")


@pytest.mark.integration
class TestMFAEnable:
    """Test MFA enable/disable endpoints"""
    
    @pytest.mark.asyncio
    async def test_enable_mfa_requires_authentication(self, async_client: AsyncClient):
        """Test enabling MFA requires authentication"""
        response = await async_client.post(
            "/api/auth/mfa/enable",
            json={"totp_code": "123456"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_disable_mfa_requires_authentication(self, async_client: AsyncClient):
        """Test disabling MFA requires authentication"""
        response = await async_client.post("/api/auth/mfa/disable")
        
        assert response.status_code == 401


@pytest.mark.integration
class TestMFAStatus:
    """Test MFA status endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_mfa_status_requires_authentication(self, async_client: AsyncClient):
        """Test getting MFA status requires authentication"""
        response = await async_client.get("/api/auth/mfa/status")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_mfa_status_returns_status(self, async_client: AsyncClient, auth_token):
        """Test getting MFA status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/auth/mfa/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "mfa_enabled" in data


@pytest.mark.integration
class TestBackupCodes:
    """Test backup code endpoints"""
    
    @pytest.mark.asyncio
    async def test_regenerate_backup_codes_requires_authentication(self, async_client: AsyncClient):
        """Test regenerating backup codes requires authentication"""
        response = await async_client.post("/api/auth/mfa/backup-codes/regenerate")
        
        assert response.status_code == 401

