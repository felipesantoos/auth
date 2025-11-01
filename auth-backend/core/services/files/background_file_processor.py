"""
Background File Processor
Processes files asynchronously in background
"""
from typing import Dict
from core.interfaces.secondary import IFileStorage
from infra.storage.image_processor import ImageProcessor
from infra.storage.video_processor import VideoProcessor
from infra.database.repositories.file_repository import FileRepository
import logging

logger = logging.getLogger(__name__)


class BackgroundFileProcessor:
    """
    Process files in background.
    
    Generates thumbnails, responsive images, video compression, etc.
    """
    
    def __init__(
        self,
        storage: IFileStorage,
        file_repository: FileRepository,
        image_processor: ImageProcessor,
        video_processor: VideoProcessor
    ):
        self.storage = storage
        self.file_repository = file_repository
        self.image_processor = image_processor
        self.video_processor = video_processor
    
    async def process_image_async(
        self,
        file_id: str,
        content: bytes
    ) -> Dict:
        """
        Process image in background.
        
        - Generate thumbnails (small, medium, large)
        - Generate responsive images (320, 640, 1280, 1920)
        - Upload all variants to storage
        """
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            logger.error(f"File not found for processing: {file_id}")
            return {"status": "error", "message": "File not found"}
        
        try:
            # Get user directory
            user_id = file_record.user_id
            
            # Generate thumbnails
            thumbnails = await self.image_processor.create_thumbnails(content)
            
            thumb_urls = {}
            for size_name, thumb_bytes in thumbnails.items():
                thumb_file = await self.storage.upload_bytes(
                    thumb_bytes,
                    f"{file_record.original_filename}_{size_name}.webp",
                    "image/webp",
                    directory=f"images/{user_id}/thumbnails"
                )
                thumb_urls[f"thumb_{size_name}"] = thumb_file.public_url
            
            # Generate responsive images
            responsive = await self.image_processor.create_responsive_images(content)
            
            responsive_urls = {}
            for width, img_bytes in responsive.items():
                resp_file = await self.storage.upload_bytes(
                    img_bytes,
                    f"{file_record.original_filename}_w{width}.webp",
                    "image/webp",
                    directory=f"images/{user_id}/responsive"
                )
                responsive_urls[f"w{width}"] = resp_file.public_url
            
            # Update file metadata with variant URLs
            file_record.metadata = file_record.metadata or {}
            file_record.metadata['thumbnails'] = thumb_urls
            file_record.metadata['responsive'] = responsive_urls
            
            logger.info(f"Image processed successfully: {file_id}")
            
            return {
                "status": "success",
                "file_id": file_id,
                "thumbnails": thumb_urls,
                "responsive": responsive_urls
            }
        
        except Exception as e:
            logger.error(f"Image processing failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    async def process_video_async(
        self,
        file_id: str,
        content: bytes
    ) -> Dict:
        """
        Process video in background.
        
        - Extract thumbnail
        - Optionally compress
        """
        file_record = await self.file_repository.get(file_id)
        
        if not file_record:
            logger.error(f"File not found for processing: {file_id}")
            return {"status": "error", "message": "File not found"}
        
        try:
            user_id = file_record.user_id
            
            # Extract thumbnail
            thumb_bytes = await self.video_processor.extract_thumbnail(content)
            thumb_file = await self.storage.upload_bytes(
                thumb_bytes,
                f"{file_record.original_filename}_thumb.jpg",
                "image/jpeg",
                directory=f"videos/{user_id}/thumbnails"
            )
            
            # Update file metadata
            file_record.metadata = file_record.metadata or {}
            file_record.metadata['thumbnail_url'] = thumb_file.public_url
            
            logger.info(f"Video processed successfully: {file_id}")
            
            return {
                "status": "success",
                "file_id": file_id,
                "thumbnail_url": thumb_file.public_url
            }
        
        except Exception as e:
            logger.error(f"Video processing failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

