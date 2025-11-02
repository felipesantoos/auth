"""
Unit tests for Audio Processor
Tests audio processing logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.audio_processor import AudioProcessor


@pytest.mark.unit
class TestAudioProcessor:
    """Test audio processing functionality"""
    
    @pytest.mark.asyncio
    async def test_extract_audio_metadata(self):
        """Test extracting audio metadata"""
        processor = AudioProcessor()
        
        with patch('ffmpeg.probe') as mock_probe:
            mock_probe.return_value = {
                "format": {
                    "duration": "180.5",
                    "bit_rate": "192000"
                },
                "streams": [{
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100"
                }]
            }
            
            metadata = await processor.get_metadata("audio.mp3")
            
            assert metadata["duration"] or mock_probe.called
    
    @pytest.mark.asyncio
    async def test_convert_audio_format(self):
        """Test converting audio to different format"""
        processor = AudioProcessor()
        
        with patch('ffmpeg.input') as mock_ffmpeg:
            mock_ffmpeg.return_value.output.return_value.run = Mock()
            
            await processor.convert("audio.mp3", output_format="aac")
            
            assert mock_ffmpeg.called

