"""
Image Processing Service Interface (Primary Port)
Defines the contract for image processing operations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from fastapi import UploadFile


class IImageProcessingService(ABC):
    """
    Image processing service interface (primary port).
    
    Defines business operations for image processing.
    """
    
    @abstractmethod
    async def upload_and_process_image(
        self,
        file: UploadFile,
        user_id: str,
        client_id: str,
        create_thumbnails: bool = True,
        create_responsive: bool = True,
        add_watermark: bool = False,
        watermark_text: str = None
    ) -> Dict:
        """
        Upload image with automatic processing.
        
        Args:
            file: Upload file
            user_id: User ID
            client_id: Client ID
            create_thumbnails: Generate thumbnails (small, medium, large)
            create_responsive: Generate responsive sizes (320, 640, 1280, 1920)
            add_watermark: Add watermark to image
            watermark_text: Watermark text
            
        Returns:
            Dict with URLs for original and all variants
        """
        pass
    
    @abstractmethod
    async def optimize_image(
        self,
        image_bytes: bytes,
        format: str = 'WEBP',
        quality: int = 85,
        max_width: int = 2048,
        max_height: int = 2048
    ) -> bytes:
        """
        Optimize image for web.
        
        Args:
            image_bytes: Original image content
            format: Output format (WEBP, JPEG, PNG)
            quality: Quality (1-100)
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Optimized image bytes
        """
        pass
    
    @abstractmethod
    async def create_thumbnails(
        self,
        image_bytes: bytes,
        sizes: Dict[str, Tuple[int, int]] = None
    ) -> Dict[str, bytes]:
        """
        Create multiple thumbnail sizes.
        
        Args:
            image_bytes: Original image
            sizes: Dict of size_name -> (width, height)
            
        Returns:
            Dict of size_name -> thumbnail bytes
        """
        pass
    
    @abstractmethod
    async def create_responsive_images(
        self,
        image_bytes: bytes,
        widths: List[int] = None
    ) -> Dict[int, bytes]:
        """
        Create responsive image sizes.
        
        Args:
            image_bytes: Original image
            widths: List of widths to generate
            
        Returns:
            Dict of width -> image bytes
        """
        pass
    
    @abstractmethod
    async def add_watermark(
        self,
        image_bytes: bytes,
        watermark_text: str,
        position: str = 'bottom-right',
        opacity: int = 128
    ) -> bytes:
        """
        Add text watermark to image.
        
        Args:
            image_bytes: Original image
            watermark_text: Text to add
            position: Position (bottom-right, bottom-left, top-right, top-left)
            opacity: Opacity (0-255)
            
        Returns:
            Image with watermark
        """
        pass
    
    @abstractmethod
    async def extract_dominant_colors(
        self,
        image_bytes: bytes,
        num_colors: int = 5
    ) -> List[str]:
        """
        Extract dominant colors from image.
        
        Args:
            image_bytes: Image content
            num_colors: Number of colors to extract
            
        Returns:
            List of hex color codes
        """
        pass

