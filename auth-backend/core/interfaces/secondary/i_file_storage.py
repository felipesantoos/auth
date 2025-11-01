"""
File Storage Interface (Secondary Port)
Defines the contract for file storage operations following hexagonal architecture
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StorageProvider(str, Enum):
    """Storage provider types."""
    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"
    CLOUDINARY = "cloudinary"
    CLOUDFLARE = "cloudflare"


@dataclass
class UploadedFile:
    """Uploaded file metadata."""
    id: str
    original_filename: str
    stored_filename: str
    file_path: str  # Storage path/key
    file_size: int  # Bytes
    mime_type: str
    checksum: str  # MD5/SHA256 hash
    uploaded_by: str
    storage_provider: StorageProvider
    public_url: Optional[str] = None
    cdn_url: Optional[str] = None
    metadata: Optional[Dict] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
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
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)


class IFileStorage(ABC):
    """
    File storage interface (secondary port).
    
    Abstracts file storage operations to allow multiple implementations
    (Local, S3, Azure, GCS, Cloudinary, etc.) without changing business logic.
    """
    
    @abstractmethod
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """
        Upload file to storage.
        
        Args:
            file_content: Binary file content
            filename: Original filename
            mime_type: MIME type of file
            directory: Directory/prefix to store file
            metadata: Optional metadata to attach to file
            
        Returns:
            UploadedFile with complete metadata
            
        Raises:
            Exception: If upload fails
        """
        pass
    
    @abstractmethod
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
        directory: str = "uploads"
    ) -> UploadedFile:
        """
        Upload bytes directly.
        
        Args:
            content: File content as bytes
            filename: Original filename
            mime_type: MIME type
            directory: Directory/prefix to store file
            
        Returns:
            UploadedFile with complete metadata
        """
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage.
        
        Args:
            file_path: Path/key of file in storage
            
        Returns:
            File content as bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Path/key of file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """
        Get public or signed URL for file.
        
        Args:
            file_path: Path/key of file
            expiration: Optional expiration time in seconds (for signed URLs)
            
        Returns:
            URL to access the file
        """
        pass
    
    @abstractmethod
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """
        Generate presigned URL for direct upload.
        
        Allows frontend to upload directly to storage without going through backend.
        
        Args:
            filename: Original filename
            mime_type: MIME type
            expiration: Expiration time in seconds (default 1 hour)
            
        Returns:
            Dict with 'url', 'fields', 'file_path', 'file_id', 'expires_in'
            
        Raises:
            NotImplementedError: If provider doesn't support presigned URLs
        """
        pass
    
    @abstractmethod
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """
        Copy file within storage.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            
        Returns:
            True if copied successfully
        """
        pass
    
    @abstractmethod
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """
        Move file within storage.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            
        Returns:
            True if moved successfully
        """
        pass
    
    @abstractmethod
    async def list_files(self, directory: str) -> List[Dict]:
        """
        List files in directory.
        
        Args:
            directory: Directory/prefix to list
            
        Returns:
            List of file metadata dicts
        """
        pass
    
    @abstractmethod
    async def get_file_metadata(self, file_path: str) -> Dict:
        """
        Get file metadata.
        
        Args:
            file_path: Path/key of file
            
        Returns:
            Dict with file metadata (size, type, last_modified, etc.)
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

