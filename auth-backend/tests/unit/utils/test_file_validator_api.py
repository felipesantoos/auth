"""
Unit tests for File Validator (API Utils)
Tests file validation logic without external dependencies
"""
import pytest
from unittest.mock import Mock
from app.api.utils.file_validator import (
    validate_file_size,
    validate_file_type,
    is_allowed_mime_type,
    get_file_extension,
    validate_filename
)


@pytest.mark.unit
class TestFileSizeValidation:
    """Test file size validation"""
    
    def test_validate_file_size_under_limit(self):
        """Test file under size limit passes validation"""
        file_mock = Mock()
        file_mock.size = 1024 * 1024  # 1MB
        
        # Should not raise
        validate_file_size(file_mock, max_size_mb=10)
    
    def test_validate_file_size_over_limit_raises_error(self):
        """Test file over size limit raises error"""
        file_mock = Mock()
        file_mock.size = 100 * 1024 * 1024  # 100MB
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_file_size(file_mock, max_size_mb=10)
    
    def test_validate_file_size_zero_raises_error(self):
        """Test zero-size file raises error"""
        file_mock = Mock()
        file_mock.size = 0
        
        with pytest.raises(ValueError, match="empty"):
            validate_file_size(file_mock, max_size_mb=10)


@pytest.mark.unit
class TestFileTypeValidation:
    """Test file type validation"""
    
    def test_validate_file_type_allowed(self):
        """Test allowed file type passes validation"""
        file_mock = Mock()
        file_mock.content_type = "image/jpeg"
        
        # Should not raise
        validate_file_type(file_mock, allowed_types=["image/jpeg", "image/png"])
    
    def test_validate_file_type_not_allowed_raises_error(self):
        """Test disallowed file type raises error"""
        file_mock = Mock()
        file_mock.content_type = "application/x-executable"
        
        with pytest.raises(ValueError, match="not allowed"):
            validate_file_type(file_mock, allowed_types=["image/jpeg", "image/png"])
    
    def test_is_allowed_mime_type(self):
        """Test MIME type checking"""
        assert is_allowed_mime_type("image/jpeg", ["image/jpeg", "image/png"]) is True
        assert is_allowed_mime_type("application/exe", ["image/jpeg"]) is False


@pytest.mark.unit
class TestFilenameValidation:
    """Test filename validation"""
    
    def test_validate_filename_safe(self):
        """Test safe filename passes validation"""
        safe_names = [
            "document.pdf",
            "photo_2024.jpg",
            "report-final.docx",
            "data (1).xlsx"
        ]
        
        for filename in safe_names:
            # Should not raise
            validate_filename(filename)
    
    def test_validate_filename_with_path_traversal_raises_error(self):
        """Test filename with path traversal raises error"""
        dangerous_names = [
            "../etc/passwd",
            "../../secret.txt",
            "..\\windows\\system32\\config"
        ]
        
        for filename in dangerous_names:
            with pytest.raises(ValueError, match="dangerous"):
                validate_filename(filename)
    
    def test_validate_filename_with_null_byte_raises_error(self):
        """Test filename with null byte raises error"""
        filename = "file\x00.pdf"
        
        with pytest.raises(ValueError, match="dangerous"):
            validate_filename(filename)
    
    def test_get_file_extension(self):
        """Test getting file extension"""
        assert get_file_extension("document.pdf") == "pdf"
        assert get_file_extension("photo.JPG") == "jpg"
        assert get_file_extension("archive.tar.gz") == "gz"
        assert get_file_extension("noextension") == ""

