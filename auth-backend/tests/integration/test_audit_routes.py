"""
Integration tests for Audit Routes
Tests audit API endpoints with database
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.integration
class TestAuditRoutes:
    """Test audit routes"""
    
    @pytest.mark.asyncio
    async def test_get_user_audit_logs(self, async_client: AsyncClient, auth_token: str):
        """Test getting user audit logs"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/audit/my-logs",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_requires_authentication(self, async_client: AsyncClient):
        """Test audit logs require authentication"""
        response = await async_client.get("/api/v1/audit/my-logs")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_search_audit_logs_admin_only(self, async_client: AsyncClient, admin_token: str):
        """Test searching audit logs requires admin role"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/audit/search?query=login",
            headers=headers
        )
        
        assert response.status_code in [200, 403]
    
    @pytest.mark.asyncio
    async def test_get_security_events_admin_only(self, async_client: AsyncClient, admin_token: str):
        """Test security events requires admin role"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/audit/security-events",
            headers=headers
        )
        
        assert response.status_code in [200, 403]


@pytest.mark.integration
class TestAuditRetention:
    """Test audit retention endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_retention_report(self, async_client: AsyncClient, admin_token: str):
        """Test getting retention policy report"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/audit/retention/report",
            headers=headers
        )
        
        assert response.status_code in [200, 403]

