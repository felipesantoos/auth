"""
Image Processor
Advanced image processing using Pillow
"""
from PIL import Image, ImageOps, ImageDraw, ImageFont
from io import BytesIO
from typing import Tuple, List, Dict
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Advanced image processing for web optimization."""
    
    def __init__(self):
        self.max_dimension = 4096
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (600, 600)
        }
    
    async def optimize_image(
        self,
        image_bytes: bytes,
        format: str = 'WEBP',
        quality: int = 85,
        max_width: int = 2048,
        max_height: int = 2048
    ) -> bytes:
        """
        Optimize image for web (resize, compress, convert to modern formats).
        
        Supported formats:
        - AVIF: Best compression (50% smaller than JPEG, 20% smaller than WebP)
        - WEBP: Great compression (30% smaller than JPEG)
        - JPEG: Universal compatibility
        - PNG: Lossless compression
        
        Args:
            image_bytes: Original image bytes
            format: Output format (AVIF, WEBP, JPEG, PNG)
            quality: Compression quality 1-100 (higher = better quality)
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            
        Returns:
            Optimized image bytes
        """
        image = Image.open(BytesIO(image_bytes))
        
        # Strip EXIF data (privacy + smaller file), preserve rotation
        image = ImageOps.exif_transpose(image)
        
        # Resize if needed
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert RGBA to RGB if saving as JPEG
        if format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])
            image = background
        
        # Save optimized
        output = BytesIO()
        save_kwargs = {'format': format, 'quality': quality, 'optimize': True}
        
        if format.upper() == 'AVIF':
            # AVIF: Best compression (50% smaller than JPEG)
            # Requires Pillow >= 10.0.0 with pillow-avif-plugin
            try:
                save_kwargs['method'] = 'best'  # or 'fast' for faster encoding
                save_kwargs['speed'] = 4  # 0-10, lower = better compression but slower
                image.save(output, **save_kwargs)
            except Exception as e:
                logger.warning(f"AVIF encoding failed, falling back to WebP: {e}")
                # Fallback to WebP if AVIF encoding fails
                format = 'WEBP'
                save_kwargs = {'format': 'WEBP', 'quality': quality, 'optimize': True, 'method': 6}
                image.save(output, **save_kwargs)
        elif format.upper() == 'WEBP':
            # WebP: Great compression (30% smaller than JPEG)
            save_kwargs['method'] = 6  # 0-6, higher = better compression
            image.save(output, **save_kwargs)
        elif format.upper() == 'JPEG':
            # JPEG: Universal compatibility
            save_kwargs['progressive'] = True  # Progressive JPEG (better for web)
            save_kwargs['subsampling'] = 0  # Best quality chroma subsampling
            image.save(output, **save_kwargs)
        elif format.upper() == 'PNG':
            # PNG: Lossless compression
            save_kwargs['compress_level'] = 9  # 0-9, higher = better compression
            image.save(output, **save_kwargs)
        else:
            # Default to WebP
            save_kwargs['format'] = 'WEBP'
            save_kwargs['method'] = 6
            image.save(output, **save_kwargs)
        
        optimized_bytes = output.getvalue()
        
        compression_ratio = (1 - len(optimized_bytes) / len(image_bytes)) * 100
        logger.info(
            f"Image optimized: {len(image_bytes)} -> {len(optimized_bytes)} bytes "
            f"({compression_ratio:.1f}% reduction) - Format: {format}"
        )
        return optimized_bytes
    
    async def create_thumbnails(
        self,
        image_bytes: bytes,
        sizes: Dict[str, Tuple[int, int]] = None
    ) -> Dict[str, bytes]:
        """Create multiple thumbnail sizes."""
        if sizes is None:
            sizes = self.thumbnail_sizes
        
        image = Image.open(BytesIO(image_bytes))
        thumbnails = {}
        
        for name, size in sizes.items():
            thumb = image.copy()
            thumb.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = BytesIO()
            thumb.save(output, format='WEBP', quality=80, method=6)
            thumbnails[name] = output.getvalue()
        
        return thumbnails
    
    async def create_responsive_images(
        self,
        image_bytes: bytes,
        widths: List[int] = None
    ) -> Dict[int, bytes]:
        """Create responsive image sizes."""
        if widths is None:
            widths = [320, 640, 1280, 1920]
        
        image = Image.open(BytesIO(image_bytes))
        original_width = image.width
        responsive_images = {}
        
        for width in widths:
            if original_width < width:
                continue
            
            aspect_ratio = image.height / image.width
            height = int(width * aspect_ratio)
            
            resized = image.copy()
            resized.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            output = BytesIO()
            resized.save(output, format='WEBP', quality=80, method=6)
            responsive_images[width] = output.getvalue()
        
        return responsive_images
    
    async def extract_dominant_colors(
        self,
        image_bytes: bytes,
        num_colors: int = 5
    ) -> List[str]:
        """Extract dominant colors from image."""
        image = Image.open(BytesIO(image_bytes))
        image.thumbnail((100, 100), Image.Resampling.LANCZOS)
        image = image.convert('RGB')
        
        pixels = image.getdata()
        color_counts = Counter(pixels)
        dominant = color_counts.most_common(num_colors)
        
        return ['#{:02x}{:02x}{:02x}'.format(r, g, b) for (r, g, b), count in dominant]
    
    async def create_multiple_formats(
        self,
        image_bytes: bytes,
        formats: List[str] = None,
        quality: int = 85,
        max_width: int = 2048,
        max_height: int = 2048
    ) -> Dict[str, bytes]:
        """
        Create multiple format versions of an image for <picture> element.
        
        This allows serving AVIF to modern browsers, WebP to most browsers,
        and JPEG as universal fallback.
        
        Usage in HTML:
        <picture>
          <source srcset="image.avif" type="image/avif">
          <source srcset="image.webp" type="image/webp">
          <img src="image.jpg" alt="Description">
        </picture>
        
        Args:
            image_bytes: Original image
            formats: List of formats to generate (default: ['AVIF', 'WEBP', 'JPEG'])
            quality: Compression quality
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Dict mapping format name to image bytes
            
        Example:
            >>> formats = await processor.create_multiple_formats(image_bytes)
            >>> avif_bytes = formats['AVIF']
            >>> webp_bytes = formats['WEBP']
            >>> jpeg_bytes = formats['JPEG']
        """
        if formats is None:
            formats = ['AVIF', 'WEBP', 'JPEG']
        
        results = {}
        
        for fmt in formats:
            try:
                optimized = await self.optimize_image(
                    image_bytes,
                    format=fmt,
                    quality=quality,
                    max_width=max_width,
                    max_height=max_height
                )
                results[fmt] = optimized
            except Exception as e:
                logger.error(f"Failed to create {fmt} format: {e}")
                continue
        
        # Log compression comparison
        if results:
            sizes = {fmt: len(data) for fmt, data in results.items()}
            logger.info(f"Format sizes: {sizes}")
        
        return results
    
    async def add_watermark(
        self,
        image_bytes: bytes,
        watermark_text: str,
        position: str = 'bottom-right',
        opacity: int = 128
    ) -> bytes:
        """Add text watermark to image."""
        image = Image.open(BytesIO(image_bytes))
        watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        try:
            font = ImageFont.truetype("Arial.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        margin = 20
        positions = {
            'bottom-right': (image.width - text_width - margin, image.height - text_height - margin),
            'bottom-left': (margin, image.height - text_height - margin),
            'top-right': (image.width - text_width - margin, margin),
            'top-left': (margin, margin)
        }
        
        x, y = positions.get(position, positions['bottom-right'])
        draw.text((x, y), watermark_text, fill=(255, 255, 255, opacity), font=font)
        
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, watermark)
        image = image.convert('RGB')
        
        output = BytesIO()
        image.save(output, format='JPEG', quality=90)
        return output.getvalue()

