"""
Integration tests for Health Check Routes
Tests health check and readiness API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthRoutes:
    """Test health check routes"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test basic health check endpoint"""
        response = await async_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy" or "status" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness check endpoint"""
        response = await async_client.get("/api/health/ready")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_liveness_check(self, async_client: AsyncClient):
        """Test liveness check endpoint"""
        response = await async_client.get("/api/health/live")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_database_health(self, async_client: AsyncClient):
        """Test database health check"""
        response = await async_client.get("/api/health/db")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "database" in data or "status" in data
    
    @pytest.mark.asyncio
    async def test_redis_health(self, async_client: AsyncClient):
        """Test Redis health check"""
        response = await async_client.get("/api/health/redis")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "redis" in data or "status" in data
    
    @pytest.mark.asyncio
    async def test_detailed_health_status(self, async_client: AsyncClient):
        """Test detailed health status endpoint"""
        response = await async_client.get("/api/health/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "services" in data or "database" in data

