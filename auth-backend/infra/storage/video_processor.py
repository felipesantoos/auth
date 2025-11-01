"""
Video Processor
Process videos using FFmpeg
"""
import subprocess
import tempfile
import os
import asyncio
import json
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos using FFmpeg."""
    
    async def compress_video(
        self,
        input_bytes: bytes,
        output_format: str = 'mp4',
        quality: str = 'medium'
    ) -> bytes:
        """
        Compress video.
        
        Quality presets:
        - low: CRF 28 (small file, lower quality)
        - medium: CRF 23 (balanced)
        - high: CRF 18 (larger file, better quality)
        """
        crf_values = {'low': 28, 'medium': 23, 'high': 18}
        crf = crf_values.get(quality, 23)
        
        # Create temp files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_file.write(input_bytes)
            input_path = input_file.name
        
        output_path = input_path.replace('.mp4', f'_compressed.{output_format}')
        
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',  # Video codec
                '-crf', str(crf),  # Quality
                '-preset', 'medium',  # Encoding speed
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Enable streaming
                '-y',  # Overwrite
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
            # Read compressed video
            with open(output_path, 'rb') as f:
                compressed_bytes = f.read()
            
            logger.info(
                f"Video compressed: {len(input_bytes)} -> {len(compressed_bytes)} bytes "
                f"({(1 - len(compressed_bytes) / len(input_bytes)) * 100:.1f}% reduction)"
            )
            
            return compressed_bytes
        
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    async def extract_thumbnail(
        self,
        video_bytes: bytes,
        timestamp: str = '00:00:01'
    ) -> bytes:
        """Extract thumbnail from video at specific timestamp."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_file.write(video_bytes)
            video_path = video_file.name
        
        thumb_path = video_path.replace('.mp4', '.jpg')
        
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', timestamp,  # Seek to timestamp
                '-vframes', '1',  # Extract 1 frame
                '-q:v', '2',  # Quality (2 is very high)
                '-y',
                thumb_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                raise Exception("Failed to extract thumbnail")
            
            with open(thumb_path, 'rb') as f:
                return f.read()
        
        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)
            if os.path.exists(thumb_path):
                os.unlink(thumb_path)
    
    async def get_video_info(self, video_bytes: bytes) -> Dict:
        """Get video metadata using ffprobe."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_file.write(video_bytes)
            video_path = video_file.name
        
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception("ffprobe failed")
            
            info = json.loads(stdout.decode())
            
            # Extract useful metadata
            video_stream = next(
                (s for s in info.get('streams', []) if s.get('codec_type') == 'video'),
                None
            )
            audio_stream = next(
                (s for s in info.get('streams', []) if s.get('codec_type') == 'audio'),
                None
            )
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'size': int(info['format'].get('size', 0)),
                'format': info['format'].get('format_name', ''),
                'bitrate': int(info['format'].get('bit_rate', 0)),
                'video': {
                    'codec': video_stream.get('codec_name') if video_stream else None,
                    'width': video_stream.get('width') if video_stream else None,
                    'height': video_stream.get('height') if video_stream else None,
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream and video_stream.get('r_frame_rate') else None
                },
                'audio': {
                    'codec': audio_stream.get('codec_name') if audio_stream else None,
                    'sample_rate': audio_stream.get('sample_rate') if audio_stream else None,
                    'channels': audio_stream.get('channels') if audio_stream else None
                }
            }
        
        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)

