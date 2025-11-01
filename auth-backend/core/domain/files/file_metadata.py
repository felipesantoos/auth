"""
File Metadata Domain Model
Represents file metadata with business logic and validation
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from core.exceptions import (
    MissingRequiredFieldException,
    ValidationException,
    InvalidValueException
)


@dataclass
class FileMetadata:
    """
    Domain model for file metadata.
    
    This is pure business logic with no framework dependencies.
    Following Single Responsibility Principle and Encapsulation.
    """
    id: Optional[str]
    user_id: str
    client_id: Optional[str]  # Multi-tenant support
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int  # Bytes
    mime_type: str
    checksum: str
    storage_provider: str
    public_url: Optional[str] = None
    cdn_url: Optional[str] = None
    is_public: bool = False
    tags: List[str] = None
    metadata: dict = None
    uploaded_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def validate(self) -> None:
        """
        Validate entity according to business rules.
        
        Raises:
            ValidationException: If validation fails
        """
        # Required fields
        if not self.user_id or not self.user_id.strip():
            raise MissingRequiredFieldException("user_id")
        
        if not self.original_filename or not self.original_filename.strip():
            raise MissingRequiredFieldException("original_filename")
        
        if not self.stored_filename or not self.stored_filename.strip():
            raise MissingRequiredFieldException("stored_filename")
        
        if not self.file_path or not self.file_path.strip():
            raise MissingRequiredFieldException("file_path")
        
        if not self.mime_type or not self.mime_type.strip():
            raise MissingRequiredFieldException("mime_type")
        
        if not self.checksum or not self.checksum.strip():
            raise MissingRequiredFieldException("checksum")
        
        if not self.storage_provider or not self.storage_provider.strip():
            raise MissingRequiredFieldException("storage_provider")
        
        # File size validation
        if self.file_size <= 0:
            raise InvalidValueException("file_size", self.file_size, "must be greater than 0")
        
        # Filename validation (basic)
        dangerous_chars = ['..', '/', '\\', '\x00']
        if any(char in self.original_filename for char in dangerous_chars):
            raise ValidationException("Filename contains dangerous characters")
    
    def belongs_to_user(self, user_id: str) -> bool:
        """Check if file belongs to a specific user."""
        return self.user_id == user_id
    
    def belongs_to_client(self, client_id: str) -> bool:
        """Check if file belongs to a specific client (multi-tenant)."""
        return self.client_id == client_id
    
    def make_public(self) -> None:
        """Make file publicly accessible."""
        self.is_public = True
    
    def make_private(self) -> None:
        """Make file private."""
        self.is_public = False
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the file."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the file."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def update_metadata(self, key: str, value: any) -> None:
        """Update metadata key-value pair."""
        self.metadata[key] = value
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''
    
    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.mime_type.startswith('image/')
    
    @property
    def is_video(self) -> bool:
        """Check if file is a video."""
        return self.mime_type.startswith('video/')
    
    @property
    def is_audio(self) -> bool:
        """Check if file is audio."""
        return self.mime_type.startswith('audio/')
    
    @property
    def is_document(self) -> bool:
        """Check if file is a document."""
        document_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain'
        ]
        return self.mime_type in document_types
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)
    
    @property
    def size_kb(self) -> float:
        """Get file size in KB."""
        return self.file_size / 1024

