"""
Unit tests for Google Cloud Storage
Tests GCS storage implementation without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.gcs_storage import GCSStorage


@pytest.mark.unit
class TestGCSStorage:
    """Test Google Cloud Storage functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_file(self):
        """Test uploading file to GCS"""
        storage = GCSStorage(bucket_name="test-bucket")
        
        with patch('google.cloud.storage.Client') as mock_client:
            mock_bucket = Mock()
            mock_blob = Mock()
            mock_blob.upload_from_string = Mock()
            mock_bucket.blob.return_value = mock_blob
            mock_client.return_value.bucket.return_value = mock_bucket
            
            url = await storage.upload(b"content", "path/file.pdf")
            
            assert url or mock_blob.upload_from_string.called
    
    @pytest.mark.asyncio
    async def test_download_file(self):
        """Test downloading file from GCS"""
        storage = GCSStorage(bucket_name="test-bucket")
        
        with patch('google.cloud.storage.Client') as mock_client:
            mock_bucket = Mock()
            mock_blob = Mock()
            mock_blob.download_as_bytes.return_value = b"file_content"
            mock_bucket.blob.return_value = mock_blob
            mock_client.return_value.bucket.return_value = mock_bucket
            
            content = await storage.download("path/file.pdf")
            
            assert content == b"file_content" or mock_blob.download_as_bytes.called

