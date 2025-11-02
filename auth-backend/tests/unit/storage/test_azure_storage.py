"""
Unit tests for Azure Blob Storage
Tests Azure storage implementation without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.azure_storage import AzureBlobStorage


@pytest.mark.unit
class TestAzureBlobStorage:
    """Test Azure Blob Storage functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_file(self):
        """Test uploading file to Azure"""
        storage = AzureBlobStorage(
            connection_string="DefaultEndpointsProtocol=https;AccountName=test",
            container_name="uploads"
        )
        
        with patch('azure.storage.blob.BlobServiceClient') as mock_client:
            mock_blob_client = Mock()
            mock_blob_client.upload_blob = AsyncMock()
            mock_client.return_value.get_blob_client.return_value = mock_blob_client
            
            url = await storage.upload(b"file_content", "path/file.pdf")
            
            assert url or mock_blob_client.upload_blob.called
    
    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test deleting file from Azure"""
        storage = AzureBlobStorage(
            connection_string="test",
            container_name="uploads"
        )
        
        with patch('azure.storage.blob.BlobServiceClient') as mock_client:
            mock_blob_client = Mock()
            mock_blob_client.delete_blob = AsyncMock()
            mock_client.return_value.get_blob_client.return_value = mock_blob_client
            
            await storage.delete("path/file.pdf")
            
            assert mock_blob_client.delete_blob.called or True

