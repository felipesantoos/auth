"""
Google Cloud Storage Implementation
Stores files in Google Cloud Storage (GCS)
"""
import uuid
import hashlib
from typing import BinaryIO, Dict, List
from datetime import datetime, timedelta
from io import BytesIO
from core.interfaces.secondary import IFileStorage, UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class GCSFileStorage(IFileStorage):
    """
    Google Cloud Storage implementation.
    
    Features:
    - Signed URLs for secure access
    - Public/private buckets
    - Lifecycle management support
    - CDN integration (Cloud CDN)
    """
    
    def __init__(self):
        """Initialize GCS client."""
        try:
            from google.cloud import storage
            
            self.storage_client = storage.Client(
                project=settings.gcp_project_id
            )
            self.bucket_name = settings.gcs_bucket_name
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except ImportError:
            raise ImportError(
                "Google Cloud Storage not available. Install: pip install google-cloud-storage"
            )
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """Upload to Google Cloud Storage."""
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        blob_name = f"{directory}/{stored_filename}"
        
        content = file_content.read()
        file_size = len(content)
        checksum = hashlib.sha256(content).hexdigest()
        
        # Create blob
        blob = self.bucket.blob(blob_name)
        blob.content_type = mime_type
        blob.cache_control = 'max-age=31536000'
        
        if metadata:
            blob.metadata = metadata
        
        # Upload
        try:
            blob.upload_from_string(content, content_type=mime_type)
            logger.info(f"File uploaded to GCS: {blob_name}")
        
        except Exception as e:
            logger.error(f"GCS upload failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload to GCS: {str(e)}")
        
        # Make public (optional)
        try:
            blob.make_public()
            public_url = blob.public_url
        except:
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
        
        return UploadedFile(
            id=file_id,
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=blob_name,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by="system",
            storage_provider=StorageProvider.GCS,
            public_url=public_url,
            created_at=datetime.utcnow()
        )
    
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
        directory: str = "uploads"
    ) -> UploadedFile:
        """Upload bytes directly to GCS."""
        return await self.upload_file(
            BytesIO(content),
            filename,
            mime_type,
            directory
        )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from GCS."""
        from google.cloud.exceptions import NotFound
        
        blob = self.bucket.blob(file_path)
        
        try:
            return blob.download_as_bytes()
        except NotFound:
            raise FileNotFoundError(f"File not found: {file_path}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from GCS."""
        blob = self.bucket.blob(file_path)
        
        try:
            blob.delete()
            logger.info(f"File deleted from GCS: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from GCS: {e}")
            return False
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """Get URL for file (public or signed)."""
        blob = self.bucket.blob(file_path)
        
        if expiration:
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiration),
                method="GET"
            )
            return url
        else:
            # Public URL
            return blob.public_url
    
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """Generate signed URL for direct upload to GCS."""
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        blob_name = f"uploads/{stored_filename}"
        
        blob = self.bucket.blob(blob_name)
        
        # Generate signed URL for PUT
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="PUT",
            content_type=mime_type
        )
        
        return {
            'url': signed_url,
            'fields': {'Content-Type': mime_type},
            'file_path': blob_name,
            'file_id': file_id,
            'expires_in': expiration
        }
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy blob within GCS."""
        source_blob = self.bucket.blob(source_path)
        dest_blob = self.bucket.blob(dest_path)
        
        try:
            self.bucket.copy_blob(source_blob, self.bucket, dest_path)
            return True
        except:
            return False
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move blob within GCS."""
        if await self.copy_file(source_path, dest_path):
            return await self.delete_file(source_path)
        return False
    
    async def list_files(self, directory: str) -> List[Dict]:
        """List blobs in directory."""
        try:
            blobs = list(self.bucket.list_blobs(prefix=directory))
            
            return [
                {
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.updated.isoformat(),
                    'content_type': blob.content_type
                }
                for blob in blobs
            ]
        
        except Exception as e:
            logger.error(f"Failed to list blobs: {e}")
            return []
    
    async def get_file_metadata(self, file_path: str) -> Dict:
        """Get blob metadata from GCS."""
        from google.cloud.exceptions import NotFound
        
        blob = self.bucket.blob(file_path)
        
        try:
            blob.reload()
            
            return {
                'content_type': blob.content_type,
                'content_length': blob.size,
                'last_modified': blob.updated.isoformat(),
                'etag': blob.etag,
                'metadata': blob.metadata or {}
            }
        
        except NotFound:
            raise FileNotFoundError(f"File not found: {file_path}")

