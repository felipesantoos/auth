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
    """
    Process videos using FFmpeg.
    
    Features:
    - H.264 compression (universal compatibility)
    - H.265/HEVC compression (50% smaller, modern browsers)
    - Multiple quality levels (480p, 720p, 1080p)
    - Thumbnail extraction
    - Video metadata extraction
    - Progressive encoding for streaming
    """
    
    def __init__(self):
        """Initialize video processor."""
        self.quality_presets = {
            'low': {'crf': 28, 'preset': 'fast'},
            'medium': {'crf': 23, 'preset': 'medium'},
            'high': {'crf': 18, 'preset': 'slow'}
        }
        self.resolution_presets = {
            '480p': {'width': 854, 'height': 480},
            '720p': {'width': 1280, 'height': 720},
            '1080p': {'width': 1920, 'height': 1080}
        }
    
    async def compress_video(
        self,
        input_bytes: bytes,
        output_format: str = 'mp4',
        quality: str = 'medium',
        codec: str = 'h264'
    ) -> bytes:
        """
        Compress video with H.264 or H.265 codec.
        
        Quality presets:
        - low: CRF 28 (small file, lower quality) - for previews
        - medium: CRF 23 (balanced) - recommended for most uses
        - high: CRF 18 (larger file, better quality) - for high-quality content
        
        Codecs:
        - h264 (libx264): Universal compatibility, good compression
        - h265 (libx265): 50% better compression, modern browsers only
        
        Args:
            input_bytes: Original video bytes
            output_format: Output format (mp4, webm)
            quality: Quality preset (low, medium, high)
            codec: Video codec (h264, h265)
            
        Returns:
            Compressed video bytes
            
        Example:
            >>> # Compress with H.264 (universal)
            >>> compressed = await processor.compress_video(video_bytes, codec='h264')
            >>> 
            >>> # Compress with H.265 (50% smaller)
            >>> compressed_h265 = await processor.compress_video(video_bytes, codec='h265')
        """
        preset = self.quality_presets.get(quality, self.quality_presets['medium'])
        crf = preset['crf']
        speed_preset = preset['preset']
        
        # Create temp files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_file.write(input_bytes)
            input_path = input_file.name
        
        output_path = input_path.replace('.mp4', f'_compressed.{output_format}')
        
        try:
            # Select codec
            if codec == 'h265' or codec == 'hevc':
                video_codec = 'libx265'
                # H.265 specific options
                codec_params = ['-x265-params', 'log-level=error']
            else:
                video_codec = 'libx264'
                codec_params = []
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', video_codec,  # Video codec
                '-crf', str(crf),  # Quality (0-51, lower = better)
                '-preset', speed_preset,  # Encoding speed vs compression
                *codec_params,  # Codec-specific parameters
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Enable progressive streaming
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
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
    
    async def create_multiple_qualities(
        self,
        input_bytes: bytes,
        resolutions: list = None,
        codec: str = 'h264'
    ) -> Dict[str, bytes]:
        """
        Create multiple quality versions of a video.
        
        This is useful for adaptive streaming (HLS, DASH) where the player
        selects the appropriate quality based on bandwidth.
        
        Args:
            input_bytes: Original video bytes
            resolutions: List of resolutions (['480p', '720p', '1080p'])
            codec: Video codec (h264, h265)
            
        Returns:
            Dict mapping resolution to video bytes
            
        Example:
            >>> qualities = await processor.create_multiple_qualities(video_bytes)
            >>> video_480p = qualities['480p']
            >>> video_720p = qualities['720p']
            >>> video_1080p = qualities['1080p']
        """
        if resolutions is None:
            resolutions = ['480p', '720p', '1080p']
        
        # Create temp input file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_file:
            input_file.write(input_bytes)
            input_path = input_file.name
        
        results = {}
        
        try:
            # Get original video dimensions
            info = await self.get_video_info(input_bytes)
            original_width = info['video']['width']
            original_height = info['video']['height']
            
            for resolution in resolutions:
                preset = self.resolution_presets.get(resolution)
                if not preset:
                    logger.warning(f"Unknown resolution: {resolution}")
                    continue
                
                # Skip if original is smaller than target
                if original_width < preset['width']:
                    logger.info(f"Skipping {resolution} (original is smaller)")
                    continue
                
                output_path = input_path.replace('.mp4', f'_{resolution}.mp4')
                
                try:
                    # Select codec
                    if codec == 'h265' or codec == 'hevc':
                        video_codec = 'libx265'
                        codec_params = ['-x265-params', 'log-level=error']
                    else:
                        video_codec = 'libx264'
                        codec_params = []
                    
                    cmd = [
                        'ffmpeg',
                        '-i', input_path,
                        # Scale to target resolution (maintain aspect ratio)
                        '-vf', f"scale={preset['width']}:{preset['height']}:force_original_aspect_ratio=decrease",
                        '-c:v', video_codec,
                        '-crf', '23',  # Good quality
                        '-preset', 'medium',
                        *codec_params,
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-movflags', '+faststart',
                        '-pix_fmt', 'yuv420p',
                        '-y',
                        output_path
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        logger.error(f"FFmpeg error for {resolution}: {stderr.decode()}")
                        continue
                    
                    # Read compressed video
                    with open(output_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    results[resolution] = video_bytes
                    
                    logger.info(
                        f"Created {resolution}: {len(video_bytes)} bytes "
                        f"({preset['width']}x{preset['height']})"
                    )
                
                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)
            
            return results
        
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
    
    async def compress_with_both_codecs(
        self,
        input_bytes: bytes,
        quality: str = 'medium'
    ) -> Dict[str, bytes]:
        """
        Compress video with both H.264 and H.265 for browser compatibility.
        
        Use in HTML:
        <video controls>
          <source src="video.h265.mp4" type="video/mp4; codecs=hevc">
          <source src="video.h264.mp4" type="video/mp4; codecs=avc1">
        </video>
        
        Args:
            input_bytes: Original video bytes
            quality: Quality preset
            
        Returns:
            Dict with 'h264' and 'h265' keys
            
        Example:
            >>> versions = await processor.compress_with_both_codecs(video_bytes)
            >>> h264_bytes = versions['h264']  # Universal compatibility
            >>> h265_bytes = versions['h265']  # 50% smaller, modern browsers
        """
        results = {}
        
        # H.264 (universal compatibility)
        results['h264'] = await self.compress_video(
            input_bytes,
            quality=quality,
            codec='h264'
        )
        
        # H.265 (better compression, modern browsers)
        results['h265'] = await self.compress_video(
            input_bytes,
            quality=quality,
            codec='h265'
        )
        
        # Log comparison
        logger.info(
            f"H.264: {len(results['h264'])} bytes, "
            f"H.265: {len(results['h265'])} bytes "
            f"({(1 - len(results['h265']) / len(results['h264'])) * 100:.1f}% smaller)"
        )
        
        return results

