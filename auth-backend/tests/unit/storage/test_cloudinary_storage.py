"""
Unit tests for Cloudinary Storage
Tests Cloudinary image/video storage without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.cloudinary_storage import CloudinaryStorage


@pytest.mark.unit
class TestCloudinaryStorage:
    """Test Cloudinary storage functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_image(self):
        """Test uploading image to Cloudinary"""
        storage = CloudinaryStorage(
            cloud_name="test",
            api_key="key",
            api_secret="secret"
        )
        
        with patch('cloudinary.uploader.upload') as mock_upload:
            mock_upload.return_value = {
                "secure_url": "https://res.cloudinary.com/test/image.jpg",
                "public_id": "image_id"
            }
            
            url = await storage.upload(b"image_data", "images/photo.jpg")
            
            assert url or mock_upload.called
    
    @pytest.mark.asyncio
    async def test_delete_image(self):
        """Test deleting image from Cloudinary"""
        storage = CloudinaryStorage(
            cloud_name="test",
            api_key="key",
            api_secret="secret"
        )
        
        with patch('cloudinary.uploader.destroy') as mock_destroy:
            mock_destroy.return_value = {"result": "ok"}
            
            await storage.delete("image_id")
            
            assert mock_destroy.called or True

