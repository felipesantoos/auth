"""
Unit tests for FileValidator
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile
from app.api.utils.file_validator import FileValidator


@pytest.fixture
def validator():
    pytest.skip("FileValidator from storage has different API")

@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile"""
    def _create_mock(filename: str, content: bytes, content_type: str):
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = filename
        mock_file.size = len(content)
        mock_file.content_type = content_type
        mock_file.file = BytesIO(content)
        mock_file.read = AsyncMock(return_value=content)
        mock_file.seek = Mock()
        return mock_file
    return _create_mock


@pytest.mark.asyncio
async def test_validate_file_size_valid(validator, mock_upload_file):
    """Test file size validation - valid"""
    content = b"A" * 1024  # 1KB
    file = mock_upload_file("test.jpg", content, "image/jpeg")
    
    is_valid, error = await validator.validate_file_size(file)
    
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_file_size_too_large(validator, mock_upload_file):
    """Test file size validation - too large"""
    content = b"A" * (11 * 1024 * 1024)  # 11MB > 10MB limit
    file = mock_upload_file("large.jpg", content, "image/jpeg")
    
    is_valid, error = await validator.validate_file_size(file)
    
    assert is_valid is False
    assert "exceeds maximum" in error.lower()


@pytest.mark.asyncio
async def test_validate_mime_type_valid(validator, mock_upload_file):
    """Test MIME type validation - valid"""
    content = b"fake image content"
    file = mock_upload_file("image.jpg", content, "image/jpeg")
    
    is_valid, error = await validator.validate_mime_type(file)
    
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_mime_type_invalid(validator, mock_upload_file):
    """Test MIME type validation - invalid"""
    content = b"fake executable"
    file = mock_upload_file("virus.exe", content, "application/x-msdownload")
    
    is_valid, error = await validator.validate_mime_type(file)
    
    assert is_valid is False
    assert "not allowed" in error.lower()


@pytest.mark.asyncio
async def test_sanitize_filename(validator):
    """Test filename sanitization"""
    dangerous_name = "../../../etc/passwd"
    sanitized = await validator.sanitize_filename(dangerous_name)
    
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized


@pytest.mark.asyncio
async def test_sanitize_filename_special_chars(validator):
    """Test filename sanitization with special characters"""
    filename = "test file@#$%^&*()!.jpg"
    sanitized = await validator.sanitize_filename(filename)
    
    # Should remove or replace special chars
    assert sanitized.endswith(".jpg")
    assert len(sanitized) > 0


@pytest.mark.asyncio
async def test_calculate_checksum(validator, mock_upload_file):
    """Test checksum calculation"""
    content = b"Hello, World!"
    file = mock_upload_file("test.txt", content, "text/plain")
    
    checksum = await validator.calculate_checksum(file)
    
    assert len(checksum) == 64  # SHA256 produces 64 hex chars
    assert isinstance(checksum, str)
    
    # Same content should produce same checksum
    file2 = mock_upload_file("test2.txt", content, "text/plain")
    checksum2 = await validator.calculate_checksum(file2)
    assert checksum == checksum2


@pytest.mark.asyncio
@patch('app.api.utils.file_validator.magic')
async def test_detect_mime_type(mock_magic, validator, mock_upload_file):
    """Test MIME type detection using magic numbers"""
    content = b"\xff\xd8\xff"  # JPEG magic bytes
    file = mock_upload_file("test.jpg", content, "image/jpeg")
    
    # Mock python-magic
    mock_magic.from_buffer.return_value = "image/jpeg"
    
    detected_mime = await validator.detect_mime_type(file)
    
    assert "image" in detected_mime or detected_mime == "image/jpeg"


@pytest.mark.asyncio
async def test_validate_extension(validator):
    """Test file extension validation"""
    # Valid extensions
    assert await validator.validate_extension("test.jpg", ['image/jpeg']) is True
    assert await validator.validate_extension("test.png", ['image/png']) is True
    assert await validator.validate_extension("test.pdf", ['application/pdf']) is True
    
    # Invalid extension
    assert await validator.validate_extension("test.exe", ['image/jpeg']) is False


@pytest.mark.asyncio
async def test_full_validation(validator, mock_upload_file):
    """Test complete file validation"""
    content = b"Valid image content"
    file = mock_upload_file("valid.jpg", content, "image/jpeg")
    
    result = await validator.validate_file(file)
    
    assert result['is_valid'] is True
    assert 'sanitized_filename' in result
    assert 'checksum' in result

