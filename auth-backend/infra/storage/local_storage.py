"""
Local File Storage Implementation
Stores files on local filesystem
"""
import os
import uuid
import hashlib
import aiofiles
import mimetypes
from pathlib import Path
from typing import BinaryIO, Dict, List
from datetime import datetime
from core.interfaces.secondary import IFileStorage, UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class LocalFileStorage(IFileStorage):
    """
    Local filesystem storage implementation.
    
    Stores files in local directory. Good for:
    - Development
    - Small scale applications
    - When S3/cloud storage is not needed
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory for file storage (defaults to settings.local_storage_path)
        """
        self.base_path = base_path or getattr(settings, 'local_storage_path', 'uploads')
        self.base_url = getattr(settings, 'api_base_url', 'http://localhost:8080')
        
        # Create base directory if it doesn't exist
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """Upload file to local storage."""
        # Generate unique ID and filename
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        
        # Full directory path
        full_directory = os.path.join(self.base_path, directory)
        Path(full_directory).mkdir(parents=True, exist_ok=True)
        
        # File path
        file_path = os.path.join(directory, stored_filename)
        full_file_path = os.path.join(self.base_path, file_path)
        
        # Read content
        content = file_content.read()
        file_size = len(content)
        
        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # Write file asynchronously
        try:
            async with aiofiles.open(full_file_path, 'wb') as f:
                await f.write(content)
            
            logger.info(
                f"File uploaded to local storage",
                extra={
                    "file_id": file_id,
                    "path": file_path,
                    "size_bytes": file_size
                }
            )
        
        except Exception as e:
            logger.error(f"Local storage upload failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload to local storage: {str(e)}")
        
        # Public URL
        public_url = f"{self.base_url}/{file_path}"
        
        return UploadedFile(
            id=file_id,
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by="system",  # Will be set by service
            storage_provider=StorageProvider.LOCAL,
            public_url=public_url,
            metadata=metadata,
            created_at=datetime.utcnow()
        )
    
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
        directory: str = "uploads"
    ) -> UploadedFile:
        """Upload bytes directly to local storage."""
        from io import BytesIO
        return await self.upload_file(
            BytesIO(content),
            filename,
            mime_type,
            directory
        )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage."""
        full_path = os.path.join(self.base_path, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
        
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        full_path = os.path.join(self.base_path, file_path)
        
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"File deleted from local storage: {file_path}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """
        Get URL for file.
        
        Note: Local storage doesn't support signed URLs.
        Expiration parameter is ignored.
        """
        return f"{self.base_url}/{file_path}"
    
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """
        Generate presigned URL for direct upload.
        
        Note: Local storage doesn't support presigned URLs.
        """
        raise NotImplementedError(
            "Local storage doesn't support presigned URLs. "
            "Use regular upload endpoint instead."
        )
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy file within local storage."""
        source_full = os.path.join(self.base_path, source_path)
        dest_full = os.path.join(self.base_path, dest_path)
        
        try:
            if not os.path.exists(source_full):
                return False
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(dest_full)
            Path(dest_dir).mkdir(parents=True, exist_ok=True)
            
            # Copy file
            async with aiofiles.open(source_full, 'rb') as src:
                content = await src.read()
                async with aiofiles.open(dest_full, 'wb') as dst:
                    await dst.write(content)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move file within local storage."""
        if await self.copy_file(source_path, dest_path):
            return await self.delete_file(source_path)
        return False
    
    async def list_files(self, directory: str) -> List[Dict]:
        """List files in directory."""
        full_dir = os.path.join(self.base_path, directory)
        
        if not os.path.exists(full_dir):
            return []
        
        files = []
        try:
            for filename in os.listdir(full_dir):
                file_path = os.path.join(full_dir, filename)
                
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'key': os.path.join(directory, filename),
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'filename': filename
                    })
            
            return files
        
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def get_file_metadata(self, file_path: str) -> Dict:
        """Get file metadata from local storage."""
        full_path = os.path.join(self.base_path, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            stat = os.stat(full_path)
            mime_type, _ = mimetypes.guess_type(full_path)
            
            return {
                'content_type': mime_type or 'application/octet-stream',
                'content_length': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_path': file_path
            }
        
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise

