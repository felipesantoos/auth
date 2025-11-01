"""
Azure Blob Storage Implementation
Stores files in Microsoft Azure Blob Storage
"""
import uuid
import hashlib
from typing import BinaryIO, Dict, List
from datetime import datetime
from io import BytesIO
from core.interfaces.secondary import IFileStorage, UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class AzureBlobStorage(IFileStorage):
    """
    Azure Blob Storage implementation.
    
    Features:
    - Async blob operations
    - Metadata and cache control
    - SAS token support for private access
    - Blob tiers (Hot, Cool, Archive)
    """
    
    def __init__(self):
        """Initialize Azure Blob Storage client."""
        try:
            from azure.storage.blob.aio import BlobServiceClient
            
            self.connection_string = settings.azure_storage_connection_string
            self.container_name = settings.azure_container_name
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        except ImportError:
            raise ImportError(
                "Azure Storage not available. Install: pip install azure-storage-blob"
            )
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """Upload to Azure Blob Storage."""
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        blob_name = f"{directory}/{stored_filename}"
        
        content = file_content.read()
        file_size = len(content)
        checksum = hashlib.sha256(content).hexdigest()
        
        # Get blob client
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        # Prepare content settings
        from azure.storage.blob import ContentSettings
        content_settings = ContentSettings(
            content_type=mime_type,
            cache_control='max-age=31536000'
        )
        
        # Upload
        try:
            await blob_client.upload_blob(
                content,
                overwrite=True,
                content_settings=content_settings,
                metadata=metadata or {}
            )
            
            logger.info(f"File uploaded to Azure Blob: {blob_name}")
        
        except Exception as e:
            logger.error(f"Azure upload failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload to Azure: {str(e)}")
        
        # Get URL
        public_url = blob_client.url
        
        return UploadedFile(
            id=file_id,
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=blob_name,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by="system",
            storage_provider=StorageProvider.AZURE,
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
        """Upload bytes directly to Azure."""
        return await self.upload_file(
            BytesIO(content),
            filename,
            mime_type,
            directory
        )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Azure Blob Storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path
        )
        
        try:
            from azure.core.exceptions import ResourceNotFoundError
            
            download_stream = await blob_client.download_blob()
            return await download_stream.readall()
        
        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Azure Blob Storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path
        )
        
        try:
            await blob_client.delete_blob()
            logger.info(f"File deleted from Azure: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete from Azure: {e}")
            return False
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """Get URL for file (public or SAS token)."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path
        )
        
        if expiration:
            # Generate SAS token
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from datetime import timedelta
            
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=file_path,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiration)
            )
            
            return f"{blob_client.url}?{sas_token}"
        else:
            return blob_client.url
    
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """
        Generate SAS URL for direct upload.
        
        Note: Azure uses SAS tokens, not presigned POST like S3.
        """
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        blob_name = f"uploads/{stored_filename}"
        
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        from datetime import timedelta
        
        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(seconds=expiration)
        )
        
        return {
            'url': f"{blob_client.url}?{sas_token}",
            'fields': {},  # Azure doesn't use fields like S3
            'file_path': blob_name,
            'file_id': file_id,
            'expires_in': expiration
        }
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy blob within Azure Storage."""
        source_blob = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=source_path
        )
        dest_blob = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=dest_path
        )
        
        try:
            await dest_blob.start_copy_from_url(source_blob.url)
            return True
        except:
            return False
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move blob within Azure Storage."""
        if await self.copy_file(source_path, dest_path):
            return await self.delete_file(source_path)
        return False
    
    async def list_files(self, directory: str) -> List[Dict]:
        """List blobs in directory."""
        container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
        
        files = []
        try:
            async for blob in container_client.list_blobs(name_starts_with=directory):
                files.append({
                    'key': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat(),
                    'content_type': blob.content_settings.content_type if blob.content_settings else None
                })
            
            return files
        
        except Exception as e:
            logger.error(f"Failed to list blobs: {e}")
            return []
    
    async def get_file_metadata(self, file_path: str) -> Dict:
        """Get blob metadata."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path
        )
        
        try:
            from azure.core.exceptions import ResourceNotFoundError
            
            properties = await blob_client.get_blob_properties()
            
            return {
                'content_type': properties.content_settings.content_type,
                'content_length': properties.size,
                'last_modified': properties.last_modified.isoformat(),
                'etag': properties.etag,
                'metadata': properties.metadata or {}
            }
        
        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")

