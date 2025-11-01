"""
Video Processing Service Interface (Primary Port)
Defines the contract for video processing operations
"""
from abc import ABC, abstractmethod
from typing import Dict
from fastapi import UploadFile


class IVideoProcessingService(ABC):
    """
    Video processing service interface (primary port).
    
    Defines business operations for video processing.
    """
    
    @abstractmethod
    async def upload_and_process_video(
        self,
        file: UploadFile,
        user_id: str,
        client_id: str,
        compress: bool = True,
        generate_thumbnail: bool = True,
        quality: str = "medium"
    ) -> Dict:
        """
        Upload video with automatic processing.
        
        Args:
            file: Upload file
            user_id: User ID
            client_id: Client ID
            compress: Whether to compress video
            generate_thumbnail: Generate thumbnail from video
            quality: Compression quality (low, medium, high)
            
        Returns:
            Dict with video URL, thumbnail URL, and metadata
        """
        pass
    
    @abstractmethod
    async def compress_video(
        self,
        video_bytes: bytes,
        output_format: str = 'mp4',
        quality: str = 'medium'
    ) -> bytes:
        """
        Compress video.
        
        Args:
            video_bytes: Original video content
            output_format: Output format (mp4, webm)
            quality: Quality preset (low, medium, high)
            
        Returns:
            Compressed video bytes
        """
        pass
    
    @abstractmethod
    async def extract_thumbnail(
        self,
        video_bytes: bytes,
        timestamp: str = '00:00:01'
    ) -> bytes:
        """
        Extract thumbnail from video.
        
        Args:
            video_bytes: Video content
            timestamp: Timestamp to extract (format: HH:MM:SS)
            
        Returns:
            Thumbnail image bytes (JPEG)
        """
        pass
    
    @abstractmethod
    async def get_video_info(
        self,
        video_bytes: bytes
    ) -> Dict:
        """
        Get video metadata using ffprobe.
        
        Args:
            video_bytes: Video content
            
        Returns:
            Dict with duration, size, format, bitrate, video/audio codec info
        """
        pass

