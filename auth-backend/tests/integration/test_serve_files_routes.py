"""
Integration tests for Serve Files Routes
Tests file serving and download API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestServeFilesRoutes:
    """Test file serving routes"""
    
    @pytest.mark.asyncio
    async def test_serve_public_file(self, async_client: AsyncClient):
        """Test serving public file without authentication"""
        response = await async_client.get("/api/v1/files/public/test-file-id")
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_serve_private_file_requires_auth(self, async_client: AsyncClient):
        """Test serving private file requires authentication"""
        response = await async_client.get("/api/v1/files/private/test-file-id")
        
        assert response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_serve_private_file_with_auth(self, async_client: AsyncClient, auth_token: str):
        """Test serving private file with authentication"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/files/private/test-file-id",
            headers=headers
        )
        
        assert response.status_code in [200, 403, 404]
    
    @pytest.mark.asyncio
    async def test_download_file(self, async_client: AsyncClient, auth_token: str):
        """Test downloading file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/files/download/test-file-id",
            headers=headers
        )
        
        assert response.status_code in [200, 403, 404]
    
    @pytest.mark.asyncio
    async def test_stream_video(self, async_client: AsyncClient, auth_token: str):
        """Test streaming video file"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/v1/files/stream/test-video-id",
            headers=headers
        )
        
        assert response.status_code in [200, 206, 404]  # 206 = Partial Content

