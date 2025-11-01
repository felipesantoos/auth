"""
Audio Processor
Process audio files using FFmpeg
"""
import tempfile
import os
import asyncio
import json
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process audio using FFmpeg."""
    
    async def convert_audio(
        self,
        input_bytes: bytes,
        output_format: str = 'mp3'
    ) -> bytes:
        """Convert audio to different format."""
        with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as input_file:
            input_file.write(input_bytes)
            input_path = input_file.name
        
        output_path = input_path.replace('.audio', f'.{output_format}')
        
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-acodec', 'libmp3lame' if output_format == 'mp3' else 'aac',
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
                raise Exception(f"FFmpeg error: {stderr.decode()}")
            
            with open(output_path, 'rb') as f:
                return f.read()
        
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    async def compress_audio(
        self,
        input_bytes: bytes,
        bitrate: str = '128k'
    ) -> bytes:
        """Compress audio by reducing bitrate."""
        with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as input_file:
            input_file.write(input_bytes)
            input_path = input_file.name
        
        output_path = input_path.replace('.audio', '_compressed.mp3')
        
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-b:a', bitrate,
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.communicate()
            
            with open(output_path, 'rb') as f:
                return f.read()
        
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    async def extract_metadata(self, audio_bytes: bytes) -> Dict:
        """Extract audio metadata."""
        with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as audio_file:
            audio_file.write(audio_bytes)
            audio_path = audio_file.name
        
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            info = json.loads(stdout.decode())
            
            audio_stream = next(
                (s for s in info.get('streams', []) if s.get('codec_type') == 'audio'),
                None
            )
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'size': int(info['format'].get('size', 0)),
                'bitrate': int(info['format'].get('bit_rate', 0)),
                'codec': audio_stream.get('codec_name') if audio_stream else None,
                'sample_rate': audio_stream.get('sample_rate') if audio_stream else None,
                'channels': audio_stream.get('channels') if audio_stream else None
            }
        
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

