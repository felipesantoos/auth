"""
Unit tests for FileService
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, AsyncMock, MagicMock
from core.services.files.file_service import FileService


@pytest.fixture
def mock_storage():
    """Mock file storage"""
    storage = AsyncMock()
    storage.upload_file = AsyncMock(return_value=MagicMock(
        id="file123",
        original_filename="test.txt",
        file_path="uploads/test.txt",
        file_size=100,
        mime_type="text/plain",
        checksum="abc123",
        uploaded_by="user123",
        public_url="http://example.com/test.txt"
    ))
    storage.download_file = AsyncMock(return_value=b"File content")
    storage.delete_file = AsyncMock(return_value=True)
    storage.get_file_url = AsyncMock(return_value="http://example.com/test.txt")
    return storage


@pytest.fixture
def mock_file_repo():
    """Mock file repository"""
    repo = AsyncMock()
    repo.save = AsyncMock(return_value=MagicMock(id="file123"))
    repo.find_by_id = AsyncMock(return_value=MagicMock(
        id="file123",
        original_filename="test.txt",
        uploaded_by="user123"
    ))
    repo.delete = AsyncMock(return_value=True)
    repo.find_by_user = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_validator():
    """Mock file validator"""
    validator = AsyncMock()
    validator.validate_file = AsyncMock(return_value={
        'is_valid': True,
        'sanitized_filename': 'test.txt',
        'checksum': 'abc123',
        'mime_type': 'text/plain'
    })
    return validator


@pytest.fixture
def file_service(mock_storage, mock_file_repo, mock_validator):
    """Create FileService instance with mocks"""
    return FileService(
        file_repository=mock_file_repo,
        storage=mock_storage,
        validator=mock_validator,
        pending_upload_repository=AsyncMock(),
        file_share_repository=AsyncMock()
    )


@pytest.mark.asyncio
async def test_upload_file(file_service, mock_storage, mock_file_repo):
    """Test file upload"""
    mock_file = Mock()
    mock_file.filename = "test.txt"
    mock_file.file = BytesIO(b"content")
    mock_file.size = 7
    
    result = await file_service.upload_file(
        file=mock_file,
        user_id="user123",
        client_id="client1"
    )
    
    assert result['id'] == "file123"
    assert result['filename'] == "test.txt"
    assert mock_storage.upload_file.called
    assert mock_file_repo.save.called


@pytest.mark.asyncio
async def test_get_file(file_service, mock_file_repo):
    """Test getting file metadata"""
    result = await file_service.get_file(
        file_id="file123",
        user_id="user123"
    )
    
    assert result['id'] == "file123"
    assert mock_file_repo.find_by_id.called


@pytest.mark.asyncio
async def test_delete_file(file_service, mock_storage, mock_file_repo):
    """Test file deletion"""
    result = await file_service.delete_file(
        file_id="file123",
        user_id="user123"
    )
    
    assert result is True
    assert mock_storage.delete_file.called
    assert mock_file_repo.delete.called


@pytest.mark.asyncio
async def test_list_user_files(file_service, mock_file_repo):
    """Test listing user files"""
    mock_file_repo.find_by_user.return_value = [
        MagicMock(id="file1", original_filename="file1.txt"),
        MagicMock(id="file2", original_filename="file2.txt")
    ]
    
    result = await file_service.list_user_files(
        user_id="user123",
        client_id="client1"
    )
    
    assert len(result['files']) == 2
    assert mock_file_repo.find_by_user.called


@pytest.mark.asyncio
async def test_download_file(file_service, mock_storage):
    """Test file download"""
    content = await file_service.download_file(
        file_id="file123",
        user_id="user123"
    )
    
    assert content == b"File content"
    assert mock_storage.download_file.called

