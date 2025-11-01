"""
Celery Tasks for File Processing
Background tasks for image and video processing
"""
from infra.celery.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="process_uploaded_image")
def process_uploaded_image(file_id: str, file_path: str):
    """
    Process uploaded image in background.
    
    - Generate thumbnails
    - Generate responsive images
    - Update file metadata
    
    Args:
        file_id: File ID in database
        file_path: Path to file in storage
    """
    import asyncio
    from infra.database.database import get_db_session
    from infra.database.repositories.file_repository import FileRepository
    from infra.storage.storage_factory import StorageFactory
    from infra.storage.image_processor import ImageProcessor
    from core.services.files.background_file_processor import BackgroundFileProcessor
    
    async def _process():
        # Get database session
        async for session in get_db_session():
            storage = StorageFactory.get_default_storage()
            file_repository = FileRepository(session)
            image_processor = ImageProcessor()
            
            processor = BackgroundFileProcessor(
                storage=storage,
                file_repository=file_repository,
                image_processor=image_processor,
                video_processor=None
            )
            
            # Download file
            content = await storage.download_file(file_path)
            
            # Process
            result = await processor.process_image_async(file_id, content)
            
            logger.info(f"Background image processing completed: {result}")
            return result
    
    # Run async function
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process())


@celery_app.task(name="process_uploaded_video")
def process_uploaded_video(file_id: str, file_path: str):
    """
    Process uploaded video in background.
    
    - Extract thumbnail
    - Optionally compress
    
    Args:
        file_id: File ID in database
        file_path: Path to file in storage
    """
    import asyncio
    from infra.database.database import get_db_session
    from infra.database.repositories.file_repository import FileRepository
    from infra.storage.storage_factory import StorageFactory
    from infra.storage.video_processor import VideoProcessor
    from core.services.files.background_file_processor import BackgroundFileProcessor
    
    async def _process():
        async for session in get_db_session():
            storage = StorageFactory.get_default_storage()
            file_repository = FileRepository(session)
            video_processor = VideoProcessor()
            
            processor = BackgroundFileProcessor(
                storage=storage,
                file_repository=file_repository,
                image_processor=None,
                video_processor=video_processor
            )
            
            # Download file
            content = await storage.download_file(file_path)
            
            # Process
            result = await processor.process_video_async(file_id, content)
            
            logger.info(f"Background video processing completed: {result}")
            return result
    
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process())

