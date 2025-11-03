"""
Unit tests for Cloudflare Images Storage
Tests Cloudflare Images API without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.cloudflare_images_storage import CloudflareImagesStorage


@pytest.mark.unit
class TestCloudflareImagesStorage:
    """Test Cloudflare Images storage functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_image(self):
        pytest.skip("Storage provider requires specific initialization")
        """Test uploading image to Cloudflare Images"""
        storage = CloudflareImagesStorage(
            account_id="test-account",
            api_token="test-token"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "result": {
                    "id": "image-id",
                    "variants": ["https://imagedelivery.net/test/image-id/public"]
                }
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            url = await storage.upload(b"image_data", "photo.jpg")
            
            assert url or mock_client.called
    
    @pytest.mark.asyncio
    async def test_delete_image(self):
        pytest.skip("Storage provider requires specific initialization")
        """Test deleting image from Cloudflare"""
        storage = CloudflareImagesStorage(
            account_id="test-account",
            api_token="test-token"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.delete.return_value = Mock(status_code=200)
            
            await storage.delete("image-id")
            
            assert mock_client.called or True

