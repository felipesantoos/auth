"""
AWS S3 File Storage Implementation
Production-ready S3 storage with presigned URLs and multipart support
"""
import uuid
import hashlib
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import BinaryIO, Dict, List
from datetime import datetime
from io import BytesIO
from core.interfaces.secondary import IFileStorage, UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class S3FileStorage(IFileStorage):
    """
    AWS S3 storage implementation (production-ready).
    
    Features:
    - Presigned URLs for direct upload
    - Server-side encryption
    - Multipart upload support (handled separately by ChunkedUploadManager)
    - Signed download URLs
    - Lifecycle management support
    """
    
    def __init__(self):
        """Initialize S3 client with configuration."""
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
        )
        
        self.bucket = settings.aws_s3_bucket
        self.region = settings.aws_s3_region
        self.base_url = settings.aws_s3_base_url or \
                       f"https://{self.bucket}.s3.{self.region}.amazonaws.com"
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        filename: str,
        mime_type: str,
        directory: str = "uploads",
        metadata: Dict = None
    ) -> UploadedFile:
        """Upload file to S3 with full metadata."""
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        s3_key = f"{directory}/{stored_filename}"
        
        content = file_content.read()
        file_size = len(content)
        checksum = hashlib.sha256(content).hexdigest()
        
        s3_metadata = {
            'original-filename': filename,
            'uploaded-at': datetime.utcnow().isoformat(),
            'checksum': checksum,
            **(metadata or {})
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content,
                ContentType=mime_type,
                Metadata=s3_metadata,
                ServerSideEncryption='AES256',
                StorageClass='INTELLIGENT_TIERING',
                CacheControl='max-age=31536000',
            )
            
            logger.info(f"File uploaded to S3: {s3_key}")
        
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}", exc_info=True)
            raise Exception(f"Failed to upload to S3: {str(e)}")
        
        return UploadedFile(
            id=file_id,
            original_filename=filename,
            stored_filename=stored_filename,
            file_path=s3_key,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by="system",
            storage_provider=StorageProvider.S3,
            public_url=f"{self.base_url}/{s3_key}",
            created_at=datetime.utcnow()
        )
    
    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
        directory: str = "uploads"
    ) -> UploadedFile:
        """Upload bytes directly to S3."""
        return await self.upload_file(
            BytesIO(content),
            filename,
            mime_type,
            directory
        )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=file_path
            )
            return response['Body'].read()
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {file_path}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=file_path
            )
            logger.info(f"File deleted from S3: {file_path}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None
    ) -> str:
        """Get URL for file (public or presigned)."""
        if expiration:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket,
                        'Key': file_path
                    },
                    ExpiresIn=expiration
                )
                return url
            except ClientError as e:
                logger.error(f"Failed to generate presigned URL: {e}")
                raise
        else:
            return f"{self.base_url}/{file_path}"
    
    async def generate_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        expiration: int = 3600
    ) -> Dict:
        """Generate presigned URL for direct upload to S3."""
        file_id = str(uuid.uuid4())
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        stored_filename = f"{file_id}.{extension}" if extension else file_id
        s3_key = f"uploads/{stored_filename}"
        
        conditions = [
            {'Content-Type': mime_type},
            ['content-length-range', 1, settings.file_upload_max_size]
        ]
        
        try:
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=s3_key,
                Fields={
                    'Content-Type': mime_type,
                    'x-amz-meta-original-filename': filename
                },
                Conditions=conditions,
                ExpiresIn=expiration
            )
            
            return {
                'url': presigned_post['url'],
                'fields': presigned_post['fields'],
                'file_path': s3_key,
                'file_id': file_id,
                'expires_in': expiration
            }
        
        except ClientError as e:
            logger.error(f"Failed to generate presigned POST: {e}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    async def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy file within S3."""
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket,
                CopySource={'Bucket': self.bucket, 'Key': source_path},
                Key=dest_path
            )
            return True
        except ClientError:
            return False
    
    async def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move file within S3."""
        if await self.copy_file(source_path, dest_path):
            return await self.delete_file(source_path)
        return False
    
    async def list_files(
        self,
        directory: str,
        max_keys: int = 1000
    ) -> List[Dict]:
        """List files in S3 directory."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=directory,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag']
                })
            
            return files
        
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def get_file_metadata(self, file_path: str) -> Dict:
        """Get file metadata from S3."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=file_path
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified').isoformat(),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
        
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File not found: {file_path}")
            raise

