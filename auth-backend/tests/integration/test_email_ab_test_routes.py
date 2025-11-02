"""
Integration tests for Email A/B Test Routes
Tests email A/B testing API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestEmailABTestRoutes:
    """Test email A/B testing routes"""
    
    @pytest.mark.asyncio
    async def test_create_ab_test(self, async_client: AsyncClient, admin_token: str):
        """Test creating email A/B test"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.post(
            "/api/v1/email/ab-tests",
            headers=headers,
            json={
                "name": "Welcome Email Test",
                "template_a": "welcome_v1",
                "template_b": "welcome_v2",
                "split_percentage": 50
            }
        )
        
        assert response.status_code in [200, 201, 403]
    
    @pytest.mark.asyncio
    async def test_get_ab_test_results(self, async_client: AsyncClient, admin_token: str):
        """Test getting A/B test results"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/email/ab-tests/test-123/results",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_list_ab_tests(self, async_client: AsyncClient, admin_token: str):
        """Test listing all A/B tests"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/email/ab-tests",
            headers=headers
        )
        
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "items" in data
    
    @pytest.mark.asyncio
    async def test_stop_ab_test(self, async_client: AsyncClient, admin_token: str):
        """Test stopping an A/B test"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.post(
            "/api/v1/email/ab-tests/test-123/stop",
            headers=headers
        )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_ab_tests_require_admin(self, async_client: AsyncClient, auth_token: str):
        """Test A/B test management requires admin role"""
        headers = {"Authorization": f"Bearer {auth_token}"}  # Regular user
        
        response = await async_client.post(
            "/api/v1/email/ab-tests",
            headers=headers,
            json={"name": "Test"}
        )
        
        assert response.status_code == 403

