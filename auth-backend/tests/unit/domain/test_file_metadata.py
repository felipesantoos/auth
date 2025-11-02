"""
Unit tests for FileMetadata domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime
from core.domain.files.file_metadata import FileMetadata
from core.exceptions import (
    MissingRequiredFieldException,
    ValidationException,
    InvalidValueException
)


@pytest.mark.unit
class TestFileMetadataValidation:
    """Test file metadata validation"""
    
    def test_valid_file_metadata_passes_validation(self):
        """Test that valid file metadata passes validation"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        # Should not raise
        file.validate()
    
    def test_missing_user_id_raises_exception(self):
        """Test that missing user_id raises exception"""
        file = FileMetadata(
            id="file-123",
            user_id="",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="user_id"):
            file.validate()
    
    def test_missing_original_filename_raises_exception(self):
        """Test that missing original_filename raises exception"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="original_filename"):
            file.validate()
    
    def test_zero_file_size_raises_exception(self):
        """Test that zero file_size raises exception"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=0,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        with pytest.raises(InvalidValueException, match="must be greater than 0"):
            file.validate()
    
    def test_dangerous_characters_in_filename_raises_exception(self):
        """Test that dangerous characters in filename raise exception"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="../etc/passwd",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        with pytest.raises(ValidationException, match="dangerous characters"):
            file.validate()


@pytest.mark.unit
class TestFileMetadataOwnership:
    """Test ownership checks"""
    
    def test_belongs_to_user_returns_true_for_owner(self):
        """Test belongs_to_user returns True for file owner"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.belongs_to_user("user-123") is True
    
    def test_belongs_to_user_returns_false_for_different_user(self):
        """Test belongs_to_user returns False for different user"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.belongs_to_user("user-456") is False
    
    def test_belongs_to_client_returns_true_for_matching_client(self):
        """Test belongs_to_client returns True for matching client"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.belongs_to_client("client-123") is True
    
    def test_belongs_to_client_returns_false_for_different_client(self):
        """Test belongs_to_client returns False for different client"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.belongs_to_client("client-456") is False


@pytest.mark.unit
class TestFileMetadataVisibility:
    """Test public/private visibility"""
    
    def test_make_public_sets_is_public_to_true(self):
        """Test make_public sets is_public to True"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3",
            is_public=False
        )
        
        file.make_public()
        
        assert file.is_public is True
    
    def test_make_private_sets_is_public_to_false(self):
        """Test make_private sets is_public to False"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3",
            is_public=True
        )
        
        file.make_private()
        
        assert file.is_public is False


@pytest.mark.unit
class TestFileMetadataTags:
    """Test tag management"""
    
    def test_add_tag_adds_tag_to_list(self):
        """Test add_tag adds tag to list"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        file.add_tag("important")
        
        assert "important" in file.tags
    
    def test_add_tag_does_not_duplicate(self):
        """Test add_tag does not add duplicate tags"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3",
            tags=["important"]
        )
        
        file.add_tag("important")
        
        assert file.tags.count("important") == 1
    
    def test_remove_tag_removes_tag_from_list(self):
        """Test remove_tag removes tag from list"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3",
            tags=["important", "document"]
        )
        
        file.remove_tag("important")
        
        assert "important" not in file.tags
        assert "document" in file.tags


@pytest.mark.unit
class TestFileMetadataMetadata:
    """Test metadata management"""
    
    def test_update_metadata_adds_key_value_pair(self):
        """Test update_metadata adds key-value pair"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        file.update_metadata("author", "John Doe")
        
        assert file.metadata["author"] == "John Doe"
    
    def test_update_metadata_updates_existing_key(self):
        """Test update_metadata updates existing key"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3",
            metadata={"author": "John Doe"}
        )
        
        file.update_metadata("author", "Jane Smith")
        
        assert file.metadata["author"] == "Jane Smith"


@pytest.mark.unit
class TestFileMetadataProperties:
    """Test file metadata properties"""
    
    def test_file_extension_returns_extension(self):
        """Test file_extension returns correct extension"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.file_extension == "pdf"
    
    def test_is_image_returns_true_for_image_mime_type(self):
        """Test is_image returns True for image mime types"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="photo.jpg",
            stored_filename="abc123.jpg",
            file_path="/uploads/abc123.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.is_image is True
    
    def test_is_video_returns_true_for_video_mime_type(self):
        """Test is_video returns True for video mime types"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="video.mp4",
            stored_filename="abc123.mp4",
            file_path="/uploads/abc123.mp4",
            file_size=1024,
            mime_type="video/mp4",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.is_video is True
    
    def test_is_audio_returns_true_for_audio_mime_type(self):
        """Test is_audio returns True for audio mime types"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="song.mp3",
            stored_filename="abc123.mp3",
            file_path="/uploads/abc123.mp3",
            file_size=1024,
            mime_type="audio/mpeg",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.is_audio is True
    
    def test_is_document_returns_true_for_pdf(self):
        """Test is_document returns True for PDF"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1024,
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.is_document is True
    
    def test_size_mb_returns_size_in_megabytes(self):
        """Test size_mb returns size in megabytes"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=1048576,  # 1 MB
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.size_mb == 1.0
    
    def test_size_kb_returns_size_in_kilobytes(self):
        """Test size_kb returns size in kilobytes"""
        file = FileMetadata(
            id="file-123",
            user_id="user-123",
            client_id="client-123",
            original_filename="document.pdf",
            stored_filename="abc123.pdf",
            file_path="/uploads/abc123.pdf",
            file_size=2048,  # 2 KB
            mime_type="application/pdf",
            checksum="sha256hash",
            storage_provider="s3"
        )
        
        assert file.size_kb == 2.0

