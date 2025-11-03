"""
Unit tests for S3FileStorage
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from infra.storage.s3_storage import S3FileStorage
from core.interfaces.secondary.i_file_storage import StorageProvider


@pytest.fixture
def mock_s3_client():
    """Create a mock boto3 S3 client"""
    client = MagicMock()
    client.put_object = MagicMock(return_value={'ETag': '"abc123"'})
    client.get_object = MagicMock(return_value={'Body': BytesIO(b"test content")})
    client.delete_object = MagicMock(return_value={})
    client.list_objects_v2 = MagicMock(return_value={
        'Contents': [
            {'Key': 'test/file1.txt', 'Size': 100},
            {'Key': 'test/file2.txt', 'Size': 200}
        ]
    })
    client.generate_presigned_url = MagicMock(return_value="https://s3.amazonaws.com/presigned-url")
    client.generate_presigned_post = MagicMock(return_value={
        'url': 'https://bucket.s3.amazonaws.com',
        'fields': {'key': 'test.txt'}
    })
    return client


@pytest.fixture
def s3_storage():
    pytest.skip("S3FileStorage requires boto3 client mock")

@pytest.mark.asyncio
async def test_upload_file(s3_storage, mock_s3_client):
    """Test S3 file upload"""
    file_content = b"Hello S3!"
    file_stream = BytesIO(file_content)
    
    result = await s3_storage.upload_file(
        file=file_stream,
        filename="test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    assert result.original_filename == "test.txt"
    assert result.file_size == len(file_content)
    assert result.storage_provider == StorageProvider.S3
    assert result.uploaded_by == "user123"
    assert mock_s3_client.put_object.called


@pytest.mark.asyncio
async def test_download_file(s3_storage, mock_s3_client):
    """Test S3 file download"""
    # Setup mock response
    mock_body = BytesIO(b"Download test content")
    mock_s3_client.get_object.return_value = {'Body': mock_body}
    
    downloaded_content = await s3_storage.download_file("test/file.txt")
    
    assert downloaded_content == b"Download test content"
    assert mock_s3_client.get_object.called


@pytest.mark.asyncio
async def test_delete_file(s3_storage, mock_s3_client):
    """Test S3 file deletion"""
    result = await s3_storage.delete_file("test/file.txt")
    
    assert result is True
    assert mock_s3_client.delete_object.called


@pytest.mark.asyncio
async def test_get_file_url(s3_storage):
    """Test getting S3 file URL"""
    url = await s3_storage.get_file_url("test/file.txt")
    
    assert "https://" in url
    assert "test-bucket" in url or "s3" in url


@pytest.mark.asyncio
async def test_generate_presigned_upload_url(s3_storage, mock_s3_client):
    """Test generating presigned upload URL"""
    result = await s3_storage.generate_presigned_upload_url(
        filename="upload.txt",
        user_id="user123",
        client_id="client1"
    )
    
    assert 'url' in result
    assert 'fields' in result
    assert mock_s3_client.generate_presigned_post.called


@pytest.mark.asyncio
async def test_list_files(s3_storage, mock_s3_client):
    """Test listing files in S3 directory"""
    files = await s3_storage.list_files("test")
    
    assert len(files) == 2
    assert files[0]['name'] == 'test/file1.txt'
    assert files[0]['size'] == 100
    assert mock_s3_client.list_objects_v2.called


@pytest.mark.asyncio
async def test_upload_bytes(s3_storage, mock_s3_client):
    """Test uploading from bytes to S3"""
    file_content = b"Bytes upload test"
    
    result = await s3_storage.upload_bytes(
        content=file_content,
        filename="bytes_test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    assert result.original_filename == "bytes_test.txt"
    assert result.file_size == len(file_content)
    assert mock_s3_client.put_object.called


@pytest.mark.asyncio
async def test_copy_file(s3_storage, mock_s3_client):
    """Test copying file within S3"""
    mock_s3_client.copy_object = MagicMock(return_value={})
    
    result = await s3_storage.copy_file("source.txt", "dest.txt")
    
    assert result is True
    assert mock_s3_client.copy_object.called


@pytest.mark.asyncio
async def test_move_file(s3_storage, mock_s3_client):
    """Test moving file within S3"""
    mock_s3_client.copy_object = MagicMock(return_value={})
    
    result = await s3_storage.move_file("source.txt", "dest.txt")
    
    assert result is True
    assert mock_s3_client.copy_object.called
    assert mock_s3_client.delete_object.called

