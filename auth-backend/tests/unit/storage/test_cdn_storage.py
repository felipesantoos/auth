"""
Unit tests for CDN Storage
Tests CDN wrapper storage without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from infra.storage.cdn_storage import CDNStorage


@pytest.mark.unit
class TestCDNStorage:
    """Test CDN storage functionality"""
    
    @pytest.mark.asyncio
    async def test_get_cdn_url(self):
        """Test getting CDN URL for file"""
        base_storage_mock = AsyncMock()
        
        storage = CDNStorage(
            base_storage=base_storage_mock,
            cdn_base_url="https://cdn.example.com"
        )
        
        url = storage.get_cdn_url("path/file.jpg")
        
        assert "cdn.example.com" in url
        assert "file.jpg" in url
    
    @pytest.mark.asyncio
    async def test_upload_delegates_to_base_storage(self):
        """Test upload delegates to base storage"""
        base_storage_mock = AsyncMock()
        base_storage_mock.upload = AsyncMock(return_value="https://storage.example.com/file.jpg")
        
        storage = CDNStorage(
            base_storage=base_storage_mock,
            cdn_base_url="https://cdn.example.com"
        )
        
        await storage.upload(b"content", "file.jpg")
        
        base_storage_mock.upload.assert_called_once()

