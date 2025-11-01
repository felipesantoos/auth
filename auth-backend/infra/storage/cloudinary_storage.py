"""
Cloudinary Storage Implementation
Optimized for images and videos with automatic transformations
"""
import uuid
import hashlib
from typing import BinaryIO, Dict, List
from datetime import datetime
from core.interfaces.secondary import IFileStorage, UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class CloudinaryStorage(IFileStorage):
    """
    Cloudinary storage (best for images and videos).
    
    Features:
    - Automatic optimization
    - On-the-fly transformations
    - CDN included
    - Format conversion (WebP, AVIF)
    - Video transcoding
    """
    
    def __init__(self):
        """Initialize Cloudinary SDK."""
        try:
            import cloudinary
            
            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret,
                secure=True
            )
            
            self.cloudinary = cloudinary
        except ImportError:
            raise ImportError(
                "Cloudinary not available. Install: pip install cloudinary"
            )
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """Upload to Cloudinary."""
        import cloudinary.uploader
        
        file_id = str(uuid.uuid4())
        
        # Determine resource type
        if mime_type.startswith('image/'):
            resource_type = 'image'
        elif mime_type.startswith('video/'):
            resource_type = 'video'
        else:
            resource_type = 'raw'
        
        content = file_content.read()
        file_size = len(content)
        checksum = hashlib.sha256(content).hexdigest()
        
        # Upload
        try:
            result = cloudinary.uploader.upload(
                content,
                public_id=f"{directory}/{file_id}",
                resource_type=resource_type,
                folder=directory,
                # Optimization options
                quality='auto',
                fetch_format='auto',  # WebP for supported browsers
                # Metadata
                context=metadata or {}
            )
            
            logger.info(f"File uploaded to Cloudinary: {result['public_id']}")
        
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload to Cloudinary: {str(e)}")
        
        return UploadedFile(
            id=file_id,
            original_filename=filename,
            stored_filename=result['public_id'],
            file_path=result['public_id'],
            file_size=result.get('bytes', file_size),
            mime_type=mime_type,
            checksum=result.get('etag', checksum),
            uploaded_by="system",
            storage_provider=StorageProvider.CLOUDINARY,
            public_url=result['secure_url'],
            created_at=datetime.utcnow()
        )
    
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
        directory: str = "uploads"
    ) -> UploadedFile:
        """Upload bytes directly to Cloudinary."""
        from io import BytesIO
        return await self.upload_file(
            BytesIO(content),
            filename,
            mime_type,
            directory
        )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Cloudinary."""
        import httpx
        
        # Get URL and download
        url = self.get_cloudinary_url(file_path)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_path}")
            response.raise_for_status()
            return response.content
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Cloudinary."""
        import cloudinary.uploader
        import cloudinary.api
        
        try:
            # Determine resource type from public_id
            resource_type = 'image'  # Default
            
            result = cloudinary.uploader.destroy(
                file_path,
                resource_type=resource_type,
                invalidate=True
            )
            
            logger.info(f"File deleted from Cloudinary: {file_path}")
            return result.get('result') == 'ok'
        
        except Exception as e:
            logger.error(f"Failed to delete from Cloudinary: {e}")
            return False
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """Get URL for file."""
        # Cloudinary URLs don't expire (use signed URLs for private)
        return self.get_cloudinary_url(file_path)
    
    def get_cloudinary_url(self, public_id: str) -> str:
        """Get Cloudinary URL for public_id."""
        from cloudinary.utils import cloudinary_url
        url, _ = cloudinary_url(public_id, secure=True)
        return url
    
    def get_optimized_url(
        self,
        file_path: str,
        width: int = None,
        height: int = None,
        quality: str = 'auto',
        format: str = 'auto'
    ) -> str:
        """
        Get optimized URL with transformations.
        
        Example transformations:
        - Resize: width=800, height=600
        - Quality: quality='auto' or 'auto:best'
        - Format: format='auto' (WebP for supported browsers)
        """
        from cloudinary.utils import cloudinary_url
        
        transformation = {}
        
        if width:
            transformation['width'] = width
        if height:
            transformation['height'] = height
        
        transformation['quality'] = quality
        transformation['fetch_format'] = format
        
        url, _ = cloudinary_url(file_path, **transformation)
        return url
    
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """
        Generate upload parameters for Cloudinary.
        
        Note: Cloudinary doesn't use presigned URLs like S3.
        Returns upload preset and signature.
        """
        raise NotImplementedError(
            "Cloudinary uses different upload mechanism. "
            "Use regular upload endpoint with Cloudinary SDK."
        )
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy file within Cloudinary (not supported)."""
        raise NotImplementedError("Cloudinary doesn't support file copy")
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move file within Cloudinary (rename)."""
        import cloudinary.uploader
        
        try:
            cloudinary.uploader.rename(source_path, dest_path)
            return True
        except:
            return False
    
    async def list_files(self, directory: str) -> List[Dict]:
        """List files in Cloudinary folder."""
        import cloudinary.api
        
        try:
            result = cloudinary.api.resources(
                type='upload',
                prefix=directory,
                max_results=500
            )
            
            return [
                {
                    'key': resource['public_id'],
                    'size': resource.get('bytes', 0),
                    'last_modified': resource.get('created_at', ''),
                    'format': resource.get('format', '')
                }
                for resource in result.get('resources', [])
            ]
        
        except Exception as e:
            logger.error(f"Failed to list Cloudinary resources: {e}")
            return []
    
    async def get_file_metadata(self, file_path: str) -> Dict:
        """Get file metadata from Cloudinary."""
        import cloudinary.api
        
        try:
            result = cloudinary.api.resource(file_path)
            
            return {
                'content_type': result.get('format', ''),
                'content_length': result.get('bytes', 0),
                'last_modified': result.get('created_at', ''),
                'width': result.get('width'),
                'height': result.get('height'),
                'metadata': result.get('context', {})
            }
        
        except Exception as e:
            if 'Not Found' in str(e):
                raise FileNotFoundError(f"File not found: {file_path}")
            raise

