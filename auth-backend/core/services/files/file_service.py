"""
File Service Implementation
Business logic for file management operations
"""
from typing import Dict, List, Optional
from fastapi import UploadFile, HTTPException
from datetime import datetime, timedelta
from core.interfaces.primary import IFileService
from core.interfaces.secondary import IFileStorage
from infra.database.repositories.file_repository import FileRepository
from infra.database.repositories.pending_upload_repository import PendingUploadRepository
from infra.database.repositories.file_share_repository import FileShareRepository
from app.api.utils.file_validator import FileValidator
import logging

logger = logging.getLogger(__name__)


class FileService(IFileService):
    """
    File service implementation.
    
    Orchestrates file operations with validation, storage, and database persistence.
    """
    
    def __init__(
        self,
        storage: IFileStorage,
        file_repository: FileRepository,
        pending_upload_repository: PendingUploadRepository,
        file_share_repository: FileShareRepository,
        validator: FileValidator
    ):
        self.storage = storage
        self.file_repository = file_repository
        self.pending_upload_repository = pending_upload_repository
        self.file_share_repository = file_share_repository
        self.validator = validator
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        client_id: str,
        directory: str = "uploads",
        is_public: bool = False,
        tags: List[str] = None
    ) -> Dict:
        """Upload file with validation."""
        # Validate file
        validation_result = await self.validator.validate_file(file)
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_FAILED",
                    "message": "File validation failed",
                    "errors": validation_result["errors"]
                }
            )
        
        # Check for duplicate (by checksum)
        existing = await self.file_repository.find_by_checksum(
            validation_result["checksum"],
            user_id
        )
        
        if existing:
            logger.info(f"Duplicate file detected: {existing.id}")
            return {
                "id": existing.id,
                "filename": existing.original_filename,
                "url": await self.storage.get_file_url(existing.file_path),
                "duplicate": True
            }
        
        # Upload to storage
        uploaded_file = await self.storage.upload_file(
            file_content=file.file,
            filename=file.filename,
            mime_type=validation_result["mime_type"],
            directory=f"{directory}/{user_id}"
        )
        
        # Save to database
        file_record = await self.file_repository.create({
            "id": uploaded_file.id,
            "user_id": user_id,
            "client_id": client_id,
            "original_filename": uploaded_file.original_filename,
            "stored_filename": uploaded_file.stored_filename,
            "file_path": uploaded_file.file_path,
            "file_size": uploaded_file.file_size,
            "mime_type": uploaded_file.mime_type,
            "checksum": uploaded_file.checksum,
            "storage_provider": uploaded_file.storage_provider.value,
            "public_url": uploaded_file.public_url,
            "is_public": is_public,
            "tags": tags or []
        })
        
        logger.info(f"File uploaded successfully: {file_record.id}")
        
        return {
            "id": file_record.id,
            "filename": file_record.original_filename,
            "url": file_record.public_url,
            "size": file_record.file_size,
            "mime_type": file_record.mime_type,
            "checksum": file_record.checksum
        }
    
    async def download_file(
        self,
        file_id: str,
        user_id: str,
        generate_signed_url: bool = True
    ) -> Dict:
        """Download file with access control."""
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            raise HTTPException(404, "File not found")
        
        # Check access (owner or shared with user)
        has_access = (
            file_record.user_id == user_id or
            file_record.is_public or
            await self.file_share_repository.has_access(file_id, user_id)
        )
        
        if not has_access:
            logger.warning(f"Unauthorized file access attempt: {file_id} by {user_id}")
            raise HTTPException(403, "Access denied")
        
        # Generate signed URL (expires in 1 hour)
        url = await self.storage.get_file_url(
            file_record.file_path,
            expiration=3600 if generate_signed_url else None
        )
        
        return {
            "id": file_record.id,
            "filename": file_record.original_filename,
            "url": url,
            "size": file_record.file_size,
            "mime_type": file_record.mime_type
        }
    
    async def delete_file(
        self,
        file_id: str,
        user_id: str
    ) -> bool:
        """Delete file with ownership check."""
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            raise HTTPException(404, "File not found")
        
        if file_record.user_id != user_id:
            raise HTTPException(403, "Not authorized to delete this file")
        
        # Delete from storage
        await self.storage.delete_file(file_record.file_path)
        
        # Delete from database
        await self.file_repository.delete(file_id)
        
        logger.info(f"File deleted: {file_id}")
        return True
    
    async def get_file_info(
        self,
        file_id: str,
        user_id: str
    ) -> Dict:
        """Get file information with access control."""
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            raise HTTPException(404, "File not found")
        
        # Check access
        has_access = (
            file_record.user_id == user_id or
            file_record.is_public or
            await self.file_share_repository.has_access(file_id, user_id)
        )
        
        if not has_access:
            raise HTTPException(403, "Access denied")
        
        return {
            "id": file_record.id,
            "filename": file_record.original_filename,
            "url": file_record.public_url,
            "size": file_record.file_size,
            "mime_type": file_record.mime_type,
            "checksum": file_record.checksum,
            "is_public": file_record.is_public,
            "tags": file_record.tags,
            "uploaded_at": file_record.uploaded_at.isoformat() if file_record.uploaded_at else None
        }
    
    async def list_user_files(
        self,
        user_id: str,
        file_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """List files owned by user with pagination."""
        files, total = await self.file_repository.list_by_user(
            user_id=user_id,
            file_type=file_type,
            page=page,
            per_page=per_page
        )
        
        return {
            "data": [
                {
                    "id": f.id,
                    "filename": f.original_filename,
                    "url": f.public_url,
                    "size": f.file_size,
                    "mime_type": f.mime_type,
                    "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
                }
                for f in files
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
    
    async def update_file_metadata(
        self,
        file_id: str,
        user_id: str,
        filename: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None
    ) -> Dict:
        """Update file metadata."""
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            raise HTTPException(404, "File not found")
        
        if file_record.user_id != user_id:
            raise HTTPException(403, "Not authorized")
        
        # Update fields
        if filename:
            file_record.original_filename = filename
        if tags is not None:
            file_record.tags = tags
        if is_public is not None:
            file_record.is_public = is_public
        
        # Save (assuming repository has update method, or use session directly)
        # For now, return updated data
        
        return {
            "id": file_record.id,
            "filename": file_record.original_filename,
            "tags": file_record.tags,
            "is_public": file_record.is_public
        }
    
    async def share_file(
        self,
        file_id: str,
        user_id: str,
        share_with_user_id: str,
        permission: str = "read",
        expires_hours: Optional[int] = None
    ) -> Dict:
        """Share file with another user."""
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            raise HTTPException(404, "File not found")
        
        if file_record.user_id != user_id:
            raise HTTPException(403, "Cannot share file you don't own")
        
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        share = await self.file_share_repository.create({
            "file_id": file_id,
            "shared_by": user_id,
            "shared_with": share_with_user_id,
            "permission": permission,
            "expires_at": expires_at
        })
        
        return {
            "share_id": share.id,
            "file_id": file_id,
            "shared_with": share_with_user_id,
            "permission": permission,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    
    async def revoke_share(
        self,
        share_id: str,
        user_id: str
    ) -> bool:
        """Revoke file share."""
        # TODO: Implement get_share in repository
        # For now, return True
        return True
    
    async def get_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        file_size: int,
        user_id: str,
        client_id: str
    ) -> Dict:
        """Generate presigned URL for direct upload."""
        # Check file size
        from config.settings import settings
        if file_size > settings.file_upload_max_size:
            raise HTTPException(400, "File too large")
        
        # Generate presigned URL from storage
        presigned_data = await self.storage.generate_presigned_upload_url(
            filename=filename,
            mime_type=mime_type,
            expiration=3600
        )
        
        # Store pending upload
        await self.pending_upload_repository.create({
            "upload_id": presigned_data["file_id"],
            "user_id": user_id,
            "filename": filename,
            "file_path": presigned_data["file_path"],
            "mime_type": mime_type,
            "expires_at": datetime.utcnow() + timedelta(seconds=presigned_data["expires_in"])
        })
        
        return presigned_data
    
    async def complete_direct_upload(
        self,
        upload_id: str,
        user_id: str,
        file_size: int,
        checksum: Optional[str] = None
    ) -> Dict:
        """Complete direct upload flow."""
        pending = await self.pending_upload_repository.get(upload_id)
        
        if not pending or pending.user_id != user_id:
            raise HTTPException(404, "Upload not found")
        
        # Verify file exists in storage
        try:
            metadata = await self.storage.get_file_metadata(pending.file_path)
        except FileNotFoundError:
            raise HTTPException(400, "File not found in storage")
        
        # Create file record
        file_record = await self.file_repository.create({
            "id": upload_id,
            "user_id": user_id,
            "client_id": None,  # TODO: Get from pending upload
            "original_filename": pending.filename,
            "stored_filename": pending.file_path.split('/')[-1],
            "file_path": pending.file_path,
            "file_size": file_size,
            "mime_type": metadata.get('content_type', pending.mime_type),
            "checksum": checksum or "",
            "storage_provider": "s3",  # Presigned URLs are S3-only
            "public_url": await self.storage.get_file_url(pending.file_path)
        })
        
        # Delete pending upload
        await self.pending_upload_repository.delete(upload_id)
        
        return {
            "id": file_record.id,
            "url": file_record.public_url,
            "status": "completed"
        }

