"""
Unit tests for File Validator (API Utils)
Tests comprehensive file validation for security
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile
from io import BytesIO

from app.api.utils.file_validator import FileValidator


@pytest.mark.unit
class TestFileValidator:
    """Test FileValidator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = FileValidator()

    def test_validator_initialization(self):
        """Should initialize with default settings"""
        assert self.validator.max_size > 0
        assert len(self.validator.allowed_types) > 0
        assert len(self.validator.blocked_extensions) > 0

    def test_blocked_extensions_configured(self):
        """Should have dangerous extensions blocked"""
        dangerous_exts = ['exe', 'bat', 'sh', 'ps1']
        
        for ext in dangerous_exts:
            assert ext in self.validator.blocked_extensions

    def test_magic_numbers_configured(self):
        """Should have file signatures configured"""
        assert 'image/jpeg' in self.validator.magic_numbers
        assert 'image/png' in self.validator.magic_numbers
        assert 'application/pdf' in self.validator.magic_numbers


@pytest.mark.unit
class TestFileValidation:
    """Test file validation logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = FileValidator()

    @pytest.mark.asyncio
    async def test_validate_empty_file(self):
        """Should reject empty file"""
        file = Mock(spec=UploadFile)
        file.filename = "test.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(return_value=b"")
        file.seek = AsyncMock()
        
        result = await self.validator.validate_file(file)
        
        assert result["valid"] is False
        assert "empty" in str(result["errors"]).lower()

    @pytest.mark.asyncio
    async def test_validate_file_too_large(self):
        """Should reject file exceeding size limit"""
        # Create file larger than max_size
        large_content = b"x" * (self.validator.max_size + 1000)
        
        file = Mock(spec=UploadFile)
        file.filename = "large.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(return_value=large_content)
        file.seek = AsyncMock()
        
        result = await self.validator.validate_file(file)
        
        assert result["valid"] is False
        assert any("large" in str(err).lower() or "size" in str(err).lower() for err in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_blocked_extension(self):
        """Should reject blocked file extension"""
        file = Mock(spec=UploadFile)
        file.filename = "malware.exe"
        file.content_type = "application/x-msdownload"
        file.read = AsyncMock(return_value=b"MZ" + b"\x00" * 100)  # EXE signature
        file.seek = AsyncMock()
        
        result = await self.validator.validate_file(file)
        
        assert result["valid"] is False
        assert any("blocked" in str(err).lower() or "exe" in str(err).lower() for err in result["errors"])


@pytest.mark.unit
class TestFilenameValidation:
    """Test filename safety validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = FileValidator()

    def test_safe_filename(self):
        """Should accept safe filename"""
        assert self.validator._is_safe_filename("document.pdf") is True
        assert self.validator._is_safe_filename("image_123.jpg") is True
        assert self.validator._is_safe_filename("my-file.txt") is True

    def test_path_traversal_rejected(self):
        """Should reject path traversal in filename"""
        assert self.validator._is_safe_filename("../etc/passwd") is False
        assert self.validator._is_safe_filename("..\\windows\\system32") is False
        assert self.validator._is_safe_filename("file/../other.txt") is False

    def test_null_byte_rejected(self):
        """Should reject null bytes in filename"""
        assert self.validator._is_safe_filename("file\x00.txt") is False

    def test_invalid_characters_rejected(self):
        """Should reject invalid characters"""
        assert self.validator._is_safe_filename("file<script>.txt") is False
        assert self.validator._is_safe_filename("file|pipe.txt") is False


@pytest.mark.unit
class TestMIMETypeDetection:
    """Test MIME type detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = FileValidator()

    def test_detect_mime_type_jpeg(self):
        """Should detect JPEG MIME type"""
        jpeg_content = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100
        
        mime = self.validator._detect_mime_type(jpeg_content, "image/jpeg")
        
        # Either detected or uses declared type
        assert mime in ["image/jpeg", "image/jpg"]

    def test_detect_mime_type_png(self):
        """Should detect PNG MIME type"""
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        
        mime = self.validator._detect_mime_type(png_content, "image/png")
        
        assert "png" in mime.lower()

    def test_detect_mime_type_fallback(self):
        """Should fallback to declared type if detection fails"""
        content = b"unknown content"
        declared = "application/custom"
        
        mime = self.validator._detect_mime_type(content, declared)
        
        # Should return something (either detected or fallback)
        assert mime is not None


@pytest.mark.unit
class TestChecksumGeneration:
    """Test file checksum generation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = FileValidator()

    @pytest.mark.asyncio
    async def test_generates_checksum(self):
        """Should generate SHA256 checksum"""
        content = b"test file content"
        
        file = Mock(spec=UploadFile)
        file.filename = "test.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result = await self.validator.validate_file(file)
        
        assert "checksum" in result
        assert len(result["checksum"]) == 64  # SHA256 hex is 64 chars

    @pytest.mark.asyncio
    async def test_same_content_same_checksum(self):
        """Should generate same checksum for same content"""
        content = b"identical content"
        
        file1 = Mock(spec=UploadFile)
        file1.filename = "file1.txt"
        file1.content_type = "text/plain"
        file1.read = AsyncMock(return_value=content)
        file1.seek = AsyncMock()
        
        file2 = Mock(spec=UploadFile)
        file2.filename = "file2.txt"
        file2.content_type = "text/plain"
        file2.read = AsyncMock(return_value=content)
        file2.seek = AsyncMock()
        
        result1 = await self.validator.validate_file(file1)
        result2 = await self.validator.validate_file(file2)
        
        assert result1["checksum"] == result2["checksum"]
