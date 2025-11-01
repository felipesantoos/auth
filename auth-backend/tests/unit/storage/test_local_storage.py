"""
Unit tests for LocalFileStorage
"""
import pytest
import os
import tempfile
import shutil
from io import BytesIO
from infra.storage.local_storage import LocalFileStorage
from core.interfaces.secondary.i_file_storage import StorageProvider


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def local_storage(temp_storage_dir):
    """Create LocalFileStorage instance"""
    return LocalFileStorage(base_path=temp_storage_dir)


@pytest.mark.asyncio
async def test_upload_file(local_storage, temp_storage_dir):
    """Test file upload"""
    file_content = b"Hello, World!"
    file_stream = BytesIO(file_content)
    
    result = await local_storage.upload_file(
        file=file_stream,
        filename="test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    assert result.original_filename == "test.txt"
    assert result.file_size == len(file_content)
    assert result.storage_provider == StorageProvider.LOCAL
    assert result.uploaded_by == "user123"
    assert os.path.exists(os.path.join(temp_storage_dir, result.file_path))


@pytest.mark.asyncio
async def test_download_file(local_storage):
    """Test file download"""
    file_content = b"Download test content"
    file_stream = BytesIO(file_content)
    
    # Upload first
    upload_result = await local_storage.upload_file(
        file=file_stream,
        filename="download_test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    # Download
    downloaded_content = await local_storage.download_file(upload_result.file_path)
    
    assert downloaded_content == file_content


@pytest.mark.asyncio
async def test_delete_file(local_storage, temp_storage_dir):
    """Test file deletion"""
    file_content = b"Delete me"
    file_stream = BytesIO(file_content)
    
    # Upload first
    upload_result = await local_storage.upload_file(
        file=file_stream,
        filename="delete_test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    file_path_full = os.path.join(temp_storage_dir, upload_result.file_path)
    assert os.path.exists(file_path_full)
    
    # Delete
    delete_result = await local_storage.delete_file(upload_result.file_path)
    
    assert delete_result is True
    assert not os.path.exists(file_path_full)


@pytest.mark.asyncio
async def test_get_file_url(local_storage):
    """Test getting file URL"""
    file_content = b"URL test"
    file_stream = BytesIO(file_content)
    
    upload_result = await local_storage.upload_file(
        file=file_stream,
        filename="url_test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    url = await local_storage.get_file_url(upload_result.file_path)
    
    assert "/api/files/serve/" in url
    assert upload_result.file_path in url


@pytest.mark.asyncio
async def test_upload_bytes(local_storage):
    """Test uploading from bytes"""
    file_content = b"Bytes upload test"
    
    result = await local_storage.upload_bytes(
        content=file_content,
        filename="bytes_test.txt",
        user_id="user123",
        client_id="client1"
    )
    
    assert result.original_filename == "bytes_test.txt"
    assert result.file_size == len(file_content)
    
    # Verify content
    downloaded = await local_storage.download_file(result.file_path)
    assert downloaded == file_content


@pytest.mark.asyncio
async def test_list_files(local_storage):
    """Test listing files in directory"""
    # Upload multiple files
    for i in range(3):
        file_content = f"File {i}".encode()
        file_stream = BytesIO(file_content)
        await local_storage.upload_file(
            file=file_stream,
            filename=f"list_test_{i}.txt",
            user_id="user123",
            client_id="client1",
            directory="test_dir"
        )
    
    # List files
    files = await local_storage.list_files("test_dir")
    
    assert len(files) >= 3
    assert any("list_test_0.txt" in f['name'] for f in files)

