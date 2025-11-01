"""
Cloudflare Images Storage Implementation
Optimized image storage with automatic optimization and CDN
"""
import uuid
import hashlib
import json
from typing import BinaryIO, Dict, List
from datetime import datetime
from core.interfaces.secondary import IFileStorage, UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class CloudflareImagesStorage(IFileStorage):
    """
    Cloudflare Images (paid service).
    
    Features:
    - Automatic optimization
    - Automatic format conversion (WebP/AVIF)
    - On-the-fly resizing via URL
    - Global CDN
    - Fast delivery
    """
    
    def __init__(self):
        """Initialize Cloudflare Images."""
        self.account_id = settings.cloudflare_account_id
        self.api_token = settings.cloudflare_api_token
        self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/images/v1"
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """Upload to Cloudflare Images."""
        import httpx
        
        file_id = str(uuid.uuid4())
        content = file_content.read()
        file_size = len(content)
        checksum = hashlib.sha256(content).hexdigest()
        
        # Upload via API
        files = {'file': (filename, content, mime_type)}
        data = {'id': file_id}
        
        if metadata:
            data['metadata'] = json.dumps(metadata)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    files=files,
                    data=data,
                    headers={'Authorization': f'Bearer {self.api_token}'},
                    timeout=60.0
                )
                
                result = response.json()
                
                if not result.get('success'):
                    raise Exception(f"Upload failed: {result.get('errors')}")
                
                image_data = result['result']
                
                logger.info(f"File uploaded to Cloudflare Images: {file_id}")
                
                return UploadedFile(
                    id=file_id,
                    original_filename=filename,
                    stored_filename=file_id,
                    file_path=file_id,
                    file_size=file_size,
                    mime_type=mime_type,
                    checksum=checksum,
                    uploaded_by="system",
                    storage_provider=StorageProvider.CLOUDFLARE,
                    public_url=image_data['variants'][0],
                    cdn_url=image_data['variants'][0],
                    created_at=datetime.utcnow()
                )
        
        except Exception as e:
            logger.error(f"Cloudflare Images upload failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload to Cloudflare Images: {str(e)}")
    
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
        directory: str = "uploads"
    ) -> UploadedFile:
        """Upload bytes directly to Cloudflare Images."""
        from io import BytesIO
        return await self.upload_file(
            BytesIO(content),
            filename,
            mime_type,
            directory
        )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Cloudflare Images."""
        import httpx
        
        # Get image URL
        url = self.get_variant_url(file_path, 'public')
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_path}")
            response.raise_for_status()
            return response.content
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Cloudflare Images."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.api_url}/{file_path}",
                    headers={'Authorization': f'Bearer {self.api_token}'}
                )
                
                result = response.json()
                logger.info(f"File deleted from Cloudflare: {file_path}")
                return result.get('success', False)
        
        except Exception as e:
            logger.error(f"Failed to delete from Cloudflare: {e}")
            return False
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """Get URL for image."""
        # Cloudflare Images doesn't support expiring URLs
        return self.get_variant_url(file_path, 'public')
    
    def get_variant_url(
        self,
        image_id: str,
        variant: str = 'public',
        width: int = None,
        height: int = None,
        fit: str = 'scale-down'
    ) -> str:
        """
        Get image variant URL with transformations.
        
        Transformations are applied via URL parameters.
        Examples:
        - /width=800,height=600,fit=cover
        - /width=400,quality=85,format=auto
        """
        base_url = f"https://imagedelivery.net/{self.account_id}/{image_id}"
        
        if width or height:
            params = []
            if width:
                params.append(f"width={width}")
            if height:
                params.append(f"height={height}")
            params.append(f"fit={fit}")
            
            return f"{base_url}/{','.join(params)}"
        else:
            return f"{base_url}/{variant}"
    
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """Cloudflare Images doesn't support presigned URLs."""
        raise NotImplementedError(
            "Cloudflare Images doesn't support presigned URLs. "
            "Use regular upload endpoint."
        )
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Cloudflare Images doesn't support copy."""
        raise NotImplementedError("Cloudflare Images doesn't support file copy")
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Cloudflare Images doesn't support move."""
        raise NotImplementedError("Cloudflare Images doesn't support file move")
    
    async def list_files(self, directory: str) -> List[Dict]:
        """List images in Cloudflare Images."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    headers={'Authorization': f'Bearer {self.api_token}'},
                    params={'per_page': 100}
                )
                
                result = response.json()
                
                if not result.get('success'):
                    return []
                
                return [
                    {
                        'key': image['id'],
                        'size': 0,  # Cloudflare doesn't expose size
                        'last_modified': image.get('uploaded', ''),
                        'filename': image.get('filename', '')
                    }
                    for image in result.get('result', {}).get('images', [])
                ]
        
        except Exception as e:
            logger.error(f"Failed to list Cloudflare images: {e}")
            return []
    
    async def get_file_metadata(self, file_path: str) -> Dict:
        """Get image metadata from Cloudflare."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/{file_path}",
                    headers={'Authorization': f'Bearer {self.api_token}'}
                )
                
                result = response.json()
                
                if not result.get('success'):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                image = result['result']
                
                return {
                    'content_type': 'image/jpeg',  # Cloudflare serves optimized
                    'content_length': 0,
                    'last_modified': image.get('uploaded', ''),
                    'filename': image.get('filename', ''),
                    'variants': image.get('variants', [])
                }
        
        except Exception as e:
            if 'not found' in str(e).lower():
                raise FileNotFoundError(f"File not found: {file_path}")
            raise

