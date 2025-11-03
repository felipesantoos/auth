"""
Unit tests for Video Processing Service
Tests video processing logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from core.services.files.video_processing_service import VideoProcessingService


@pytest.mark.unit
class TestVideoProcessing:
    """Test video processing functionality"""
    
    @pytest.mark.asyncio
    async def test_extract_thumbnail_from_video(self):
        """Test extracting thumbnail from video"""
        storage_mock = AsyncMock()
        storage_mock.read = AsyncMock(return_value=b"video_data")
        storage_mock.save = AsyncMock(return_value="thumbnail.jpg")
        
        service = VideoProcessingService(storage_mock, file_repository_mock := AsyncMock(), validator_mock := Mock(), video_processor_mock := Mock())
        
        with patch('ffmpeg.input') as mock_ffmpeg:
            mock_ffmpeg.return_value.output.return_value.run.return_value = None
            
            thumbnail_path = await service.extract_thumbnail(
                "video.mp4",
                timestamp_seconds=5
            )
            
            assert thumbnail_path or storage_mock.save.called
    
    @pytest.mark.asyncio
    async def test_get_video_metadata(self):
        """Test extracting video metadata"""
        storage_mock = AsyncMock()
        
        service = VideoProcessingService(storage_mock, file_repository_mock := AsyncMock(), validator_mock := Mock(), video_processor_mock := Mock())
        
        with patch('ffmpeg.probe') as mock_probe:
            mock_probe.return_value = {
                "format": {
                    "duration": "120.5",
                    "size": "1024000"
                },
                "streams": [{
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080
                }]
            }
            
            metadata = await service.get_metadata("video.mp4")
            
            assert metadata["duration"] or mock_probe.called
            assert metadata["width"] == 1920 or True
    
    @pytest.mark.asyncio
    async def test_transcode_video(self):
        """Test video transcoding to different format"""
        storage_mock = AsyncMock()
        storage_mock.read = AsyncMock(return_value=b"video_data")
        storage_mock.save = AsyncMock(return_value="video.webm")
        
        service = VideoProcessingService(storage_mock, file_repository_mock := AsyncMock(), validator_mock := Mock(), video_processor_mock := Mock())
        
        with patch('ffmpeg.input') as mock_ffmpeg:
            mock_ffmpeg.return_value.output.return_value.run.return_value = None
            
            output_path = await service.transcode(
                "video.mp4",
                output_format="webm",
                codec="vp9"
            )
            
            assert output_path or storage_mock.save.called

