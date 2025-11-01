"""
Unit tests for ChunkedUploadManager
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from core.services.files.chunked_upload_manager import ChunkedUploadManager


@pytest.fixture
def mock_multipart_repo():
    """Mock multipart upload repository"""
    repo = AsyncMock()
    repo.create = AsyncMock(return_value=MagicMock(
        id="upload123",
        file_name="large_file.zip",
        total_chunks=5,
        uploaded_chunks=0
    ))
    repo.find_by_id = AsyncMock(return_value=MagicMock(
        id="upload123",
        file_name="large_file.zip",
        total_chunks=5,
        uploaded_chunks=3,
        status="in_progress"
    ))
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_part_repo():
    """Mock upload part repository"""
    repo = AsyncMock()
    repo.save = AsyncMock(return_value=MagicMock(part_number=1))
    repo.find_by_upload_id = AsyncMock(return_value=[
        MagicMock(part_number=1, checksum="abc"),
        MagicMock(part_number=2, checksum="def")
    ])
    return repo


@pytest.fixture
def mock_storage():
    """Mock storage"""
    storage = AsyncMock()
    storage.upload_bytes = AsyncMock(return_value=MagicMock(
        id="file123",
        file_path="uploads/test.txt"
    ))
    return storage


@pytest.fixture
def chunked_manager(mock_multipart_repo, mock_part_repo, mock_storage):
    """Create ChunkedUploadManager instance"""
    return ChunkedUploadManager(
        multipart_repository=mock_multipart_repo,
        part_repository=mock_part_repo,
        storage=mock_storage
    )


@pytest.mark.asyncio
async def test_initiate_upload(chunked_manager, mock_multipart_repo):
    """Test initiating chunked upload"""
    result = await chunked_manager.initiate_upload(
        filename="large_file.zip",
        total_size=100000000,  # 100MB
        chunk_size=5242880,    # 5MB
        user_id="user123",
        client_id="client1"
    )
    
    assert result['upload_id'] == "upload123"
    assert result['filename'] == "large_file.zip"
    assert mock_multipart_repo.create.called


@pytest.mark.asyncio
async def test_upload_chunk(chunked_manager, mock_part_repo):
    """Test uploading a single chunk"""
    chunk_data = b"A" * 1024  # 1KB chunk
    
    result = await chunked_manager.upload_chunk(
        upload_id="upload123",
        chunk_number=1,
        chunk_data=chunk_data,
        user_id="user123"
    )
    
    assert result['part_number'] == 1
    assert result['success'] is True
    assert mock_part_repo.save.called


@pytest.mark.asyncio
async def test_complete_upload(chunked_manager, mock_multipart_repo, mock_part_repo, mock_storage):
    """Test completing chunked upload"""
    result = await chunked_manager.complete_upload(
        upload_id="upload123",
        user_id="user123"
    )
    
    assert result['file_id'] == "file123"
    assert result['status'] == "completed"
    assert mock_part_repo.find_by_upload_id.called
    assert mock_storage.upload_bytes.called


@pytest.mark.asyncio
async def test_abort_upload(chunked_manager, mock_multipart_repo):
    """Test aborting chunked upload"""
    result = await chunked_manager.abort_upload(
        upload_id="upload123",
        user_id="user123"
    )
    
    assert result is True
    assert mock_multipart_repo.delete.called


@pytest.mark.asyncio
async def test_get_upload_status(chunked_manager, mock_multipart_repo):
    """Test getting upload status"""
    result = await chunked_manager.get_upload_status(
        upload_id="upload123",
        user_id="user123"
    )
    
    assert result['upload_id'] == "upload123"
    assert result['total_chunks'] == 5
    assert result['uploaded_chunks'] == 3
    assert result['progress_percent'] == 60.0


@pytest.mark.asyncio
async def test_list_pending_uploads(chunked_manager, mock_multipart_repo):
    """Test listing pending uploads"""
    mock_multipart_repo.find_by_user = AsyncMock(return_value=[
        MagicMock(id="upload1", status="in_progress"),
        MagicMock(id="upload2", status="in_progress")
    ])
    
    result = await chunked_manager.list_pending_uploads(user_id="user123")
    
    assert len(result) == 2
    assert mock_multipart_repo.find_by_user.called

