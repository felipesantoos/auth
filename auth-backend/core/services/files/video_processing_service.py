"""
Video Processing Service Implementation
Business logic for video processing operations
"""
from typing import Dict
from fastapi import UploadFile, HTTPException
from core.interfaces.primary import IVideoProcessingService
from core.interfaces.secondary import IFileStorage
from infra.storage.video_processor import VideoProcessor
from infra.database.repositories.file_repository import FileRepository
from app.api.utils.file_validator import FileValidator
import logging

logger = logging.getLogger(__name__)


class VideoProcessingService(IVideoProcessingService):
    """
    Video processing service implementation.
    
    Orchestrates video upload, processing, and storage.
    """
    
    def __init__(
        self,
        storage: IFileStorage,
        file_repository: FileRepository,
        validator: FileValidator,
        video_processor: VideoProcessor
    ):
        self.storage = storage
        self.file_repository = file_repository
        self.validator = validator
        self.video_processor = video_processor
    
    async def upload_and_process_video(
        self,
        file: UploadFile,
        user_id: str,
        client_id: str,
        compress: bool = True,
        generate_thumbnail: bool = True,
        quality: str = "medium"
    ) -> Dict:
        """Upload video with automatic processing."""
        # Validate file
        validation_result = await self.validator.validate_file(file)
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "VALIDATION_FAILED",
                    "message": "Video validation failed",
                    "errors": validation_result["errors"]
                }
            )
        
        # Read content
        content = await file.read()
        
        # Get video info
        info = await self.video_processor.get_video_info(content)
        
        # Compress if needed
        if compress and info['size'] > 50_000_000:  # > 50MB
            logger.info(f"Compressing video (original size: {info['size']} bytes)")
            compressed = await self.video_processor.compress_video(
                content,
                quality=quality
            )
        else:
            compressed = content
        
        # Upload video
        video_file = await self.storage.upload_bytes(
            compressed,
            file.filename,
            "video/mp4",
            directory=f"videos/{user_id}"
        )
        
        # Save to database
        file_record = await self.file_repository.create({
            "id": video_file.id,
            "user_id": user_id,
            "client_id": client_id,
            "original_filename": video_file.original_filename,
            "stored_filename": video_file.stored_filename,
            "file_path": video_file.file_path,
            "file_size": video_file.file_size,
            "mime_type": video_file.mime_type,
            "checksum": video_file.checksum,
            "storage_provider": video_file.storage_provider.value,
            "public_url": video_file.public_url,
            "metadata": {"video_info": info}
        })
        
        # Generate thumbnail
        thumbnail_url = None
        if generate_thumbnail:
            try:
                thumb_bytes = await self.video_processor.extract_thumbnail(compressed)
                thumb_file = await self.storage.upload_bytes(
                    thumb_bytes,
                    f"{file.filename}_thumb.jpg",
                    "image/jpeg",
                    directory=f"videos/{user_id}/thumbnails"
                )
                thumbnail_url = thumb_file.public_url
            except Exception as e:
                logger.error(f"Failed to generate thumbnail: {e}")
        
        return {
            "id": file_record.id,
            "url": file_record.public_url,
            "thumbnail_url": thumbnail_url,
            "duration": info['duration'],
            "original_size": len(content),
            "compressed_size": len(compressed),
            "video_info": info
        }
    
    async def compress_video(
        self,
        video_bytes: bytes,
        output_format: str = 'mp4',
        quality: str = 'medium'
    ) -> bytes:
        """Compress video."""
        return await self.video_processor.compress_video(
            video_bytes,
            output_format,
            quality
        )
    
    async def extract_thumbnail(
        self,
        video_bytes: bytes,
        timestamp: str = '00:00:01'
    ) -> bytes:
        """Extract thumbnail from video."""
        return await self.video_processor.extract_thumbnail(
            video_bytes,
            timestamp
        )
    
    async def get_video_info(
        self,
        video_bytes: bytes
    ) -> Dict:
        """Get video metadata."""
        return await self.video_processor.get_video_info(video_bytes)

