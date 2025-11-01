"""
Chunked Upload Manager
Manages multipart/chunked uploads for large files
"""
import uuid
import boto3
from typing import Dict
from fastapi import HTTPException
from datetime import datetime
from infra.database.repositories.multipart_upload_repository import MultipartUploadRepository
from infra.database.repositories.upload_part_repository import UploadPartRepository
from core.interfaces.secondary import UploadedFile, StorageProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class ChunkedUploadManager:
    """
    Manage chunked/multipart uploads for large files.
    
    Uses S3 multipart upload API to handle files > 100MB efficiently.
    """
    
    def __init__(
        self,
        multipart_upload_repository: MultipartUploadRepository,
        upload_part_repository: UploadPartRepository
    ):
        self.multipart_upload_repository = multipart_upload_repository
        self.upload_part_repository = upload_part_repository
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.bucket = settings.aws_s3_bucket
        self.chunk_size = 5 * 1024 * 1024  # 5MB (S3 minimum)
    
    async def initiate_multipart_upload(
        self,
        filename: str,
        mime_type: str,
        user_id: str
    ) -> Dict:
        """Initiate multipart upload."""
        file_id = str(uuid.uuid4())
        s3_key = f"uploads/{user_id}/{file_id}/{filename}"
        
        # Initiate multipart upload in S3
        response = self.s3_client.create_multipart_upload(
            Bucket=self.bucket,
            Key=s3_key,
            ContentType=mime_type,
            ServerSideEncryption='AES256'
        )
        
        upload_id = response['UploadId']
        
        # Store in database
        await self.multipart_upload_repository.create({
            "upload_id": upload_id,
            "file_id": file_id,
            "user_id": user_id,
            "filename": filename,
            "s3_key": s3_key,
            "mime_type": mime_type,
            "status": "initiated"
        })
        
        logger.info(f"Multipart upload initiated: {upload_id}")
        
        return {
            "upload_id": upload_id,
            "file_id": file_id,
            "chunk_size": self.chunk_size
        }
    
    async def upload_chunk(
        self,
        upload_id: str,
        chunk_number: int,
        chunk_data: bytes
    ) -> Dict:
        """Upload a single chunk."""
        upload = await self.multipart_upload_repository.get(upload_id)
        
        if not upload:
            raise HTTPException(404, "Upload not found")
        
        if upload.status == "aborted":
            raise HTTPException(400, "Upload has been aborted")
        
        # Upload part to S3
        response = self.s3_client.upload_part(
            Bucket=self.bucket,
            Key=upload.s3_key,
            PartNumber=chunk_number,
            UploadId=upload_id,
            Body=chunk_data
        )
        
        etag = response['ETag']
        
        # Store part info
        await self.upload_part_repository.create({
            "upload_id": upload_id,
            "part_number": chunk_number,
            "etag": etag,
            "size": len(chunk_data)
        })
        
        # Update upload status
        upload.status = "uploading"
        upload.uploaded_size = (upload.uploaded_size or 0) + len(chunk_data)
        await self.multipart_upload_repository.save(upload)
        
        logger.info(f"Chunk uploaded: {upload_id} part {chunk_number}")
        
        return {
            "part_number": chunk_number,
            "etag": etag,
            "uploaded": len(chunk_data)
        }
    
    async def complete_multipart_upload(
        self,
        upload_id: str
    ) -> UploadedFile:
        """Complete multipart upload."""
        upload = await self.multipart_upload_repository.get(upload_id)
        parts = await self.upload_part_repository.list_by_upload(upload_id)
        
        if not upload:
            raise HTTPException(404, "Upload not found")
        
        # Sort parts by number
        parts = sorted(parts, key=lambda p: p.part_number)
        
        # Build parts list for S3
        multipart_upload = {
            'Parts': [
                {'PartNumber': p.part_number, 'ETag': p.etag}
                for p in parts
            ]
        }
        
        # Complete upload in S3
        self.s3_client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=upload.s3_key,
            UploadId=upload_id,
            MultipartUpload=multipart_upload
        )
        
        # Get file size
        head = self.s3_client.head_object(
            Bucket=self.bucket,
            Key=upload.s3_key
        )
        file_size = head['ContentLength']
        
        # Update upload status
        upload.status = "completed"
        upload.completed_at = datetime.utcnow()
        await self.multipart_upload_repository.save(upload)
        
        logger.info(f"Multipart upload completed: {upload_id}")
        
        base_url = settings.aws_s3_base_url or \
                   f"https://{self.bucket}.s3.{settings.aws_s3_region}.amazonaws.com"
        
        return UploadedFile(
            id=upload.file_id,
            original_filename=upload.filename,
            stored_filename=upload.s3_key.split('/')[-1],
            file_path=upload.s3_key,
            file_size=file_size,
            mime_type=upload.mime_type,
            checksum="",  # Could calculate from parts
            uploaded_by=upload.user_id,
            storage_provider=StorageProvider.S3,
            public_url=f"{base_url}/{upload.s3_key}",
            created_at=datetime.utcnow()
        )
    
    async def abort_multipart_upload(self, upload_id: str) -> bool:
        """Abort multipart upload."""
        upload = await self.multipart_upload_repository.get(upload_id)
        
        if not upload:
            return False
        
        # Abort in S3
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket,
                Key=upload.s3_key,
                UploadId=upload_id
            )
        except:
            pass
        
        # Update status
        upload.status = "aborted"
        await self.multipart_upload_repository.save(upload)
        
        logger.info(f"Multipart upload aborted: {upload_id}")
        return True

