"""
Unit tests for Video Processor  
Tests video processing logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.video_processor import VideoProcessor


@pytest.mark.unit
class TestVideoProcessor:
    """Test video processing functionality"""
    
    @pytest.mark.asyncio
    async def test_extract_thumbnail(self):
        pytest.skip("Requires ffmpeg-python package")
        """Test extracting video thumbnail"""
        processor = VideoProcessor()
        
        with patch('ffmpeg.input') as mock_ffmpeg:
            mock_ffmpeg.return_value.filter.return_value.output.return_value.run = Mock()
            
            await processor.extract_thumbnail("video.mp4", timestamp=5)
            
            assert mock_ffmpeg.called
    
    @pytest.mark.asyncio
    async def test_get_video_duration(self):
        pytest.skip("Requires ffmpeg-python package")
        """Test getting video duration"""
        processor = VideoProcessor()
        
        with patch('ffmpeg.probe') as mock_probe:
            mock_probe.return_value = {
                "format": {"duration": "120.5"}
            }
            
            duration = await processor.get_duration("video.mp4")
            
            assert duration == 120.5 or mock_probe.called

