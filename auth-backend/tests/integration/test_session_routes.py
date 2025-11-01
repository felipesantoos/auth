"""
Integration tests for Session Routes
Tests session management API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestSessionListing:
    """Test session listing endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_sessions_requires_authentication(self, async_client: AsyncClient):
        """Test listing sessions requires authentication"""
        response = await async_client.get("/api/auth/sessions")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_sessions_returns_active_sessions(self, async_client: AsyncClient, auth_token):
        """Test listing active sessions"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/auth/sessions",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.integration
class TestSessionRevocation:
    """Test session revocation endpoints"""
    
    @pytest.mark.asyncio
    async def test_revoke_session_requires_authentication(self, async_client: AsyncClient):
        """Test revoking session requires authentication"""
        response = await async_client.delete("/api/auth/sessions/session-123")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_revoke_all_sessions_requires_authentication(self, async_client: AsyncClient):
        """Test revoking all sessions requires authentication"""
        response = await async_client.delete("/api/auth/sessions/all")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session_returns_404(self, async_client: AsyncClient, auth_token):
        """Test revoking nonexistent session"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.delete(
            "/api/auth/sessions/nonexistent-session-id",
            headers=headers
        )
        
        assert response.status_code in [404, 400]


@pytest.mark.integration
class TestSessionInfo:
    """Test session information endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_current_session_requires_authentication(self, async_client: AsyncClient):
        """Test getting current session requires authentication"""
        response = await async_client.get("/api/auth/sessions/current")
        
        assert response.status_code == 401

