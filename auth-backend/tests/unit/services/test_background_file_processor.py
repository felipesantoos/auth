"""
Unit tests for Background File Processor
Tests background file processing logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.files.background_file_processor import BackgroundFileProcessor


@pytest.mark.unit
class TestBackgroundFileProcessing:
    """Test background file processing functionality"""
    
    @pytest.mark.asyncio
    async def test_process_image_creates_thumbnails(self):
        """Test image processing creates thumbnails"""
        file_repo_mock = AsyncMock()
        storage_mock = AsyncMock()
        image_processor_mock = AsyncMock()
        image_processor_mock.create_thumbnail = AsyncMock(return_value=b"thumbnail_data")
        
        service = BackgroundFileProcessor(file_repo_mock, storage_mock, image_processor_mock, video_processor_mock := Mock())
        
        file = Mock(
            id="file-123",
            file_path="/uploads/image.jpg",
            mime_type="image/jpeg"
        )
        
        await service.process_image(file)
        
        image_processor_mock.create_thumbnail.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_video_creates_preview(self):
        """Test video processing creates preview/thumbnail"""
        file_repo_mock = AsyncMock()
        storage_mock = AsyncMock()
        video_processor_mock = AsyncMock()
        video_processor_mock.create_preview = AsyncMock(return_value=b"preview_data")
        
        service = BackgroundFileProcessor(file_repo_mock, storage_mock, image_processor_mock := Mock(), video_processor_mock)
        
        file = Mock(
            id="file-123",
            file_path="/uploads/video.mp4",
            mime_type="video/mp4"
        )
        
        await service.process_video(file)
        
        video_processor_mock.create_preview.assert_called()
    
    @pytest.mark.asyncio
    async def test_scan_file_for_viruses(self):
        """Test file virus scanning"""
        file_repo_mock = AsyncMock()
        storage_mock = AsyncMock()
        scanner_mock = AsyncMock()
        scanner_mock.scan = AsyncMock(return_value={"clean": True})
        
        service = BackgroundFileProcessor(file_repo_mock, storage_mock, image_processor_mock := Mock(), video_processor_mock := Mock())
        
        file = Mock(id="file-123", file_path="/uploads/document.pdf")
        
        result = await service.scan_file(file)
        
        assert result["clean"] is True or scanner_mock.scan.called

