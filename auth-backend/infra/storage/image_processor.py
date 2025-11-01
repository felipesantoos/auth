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
        """Optimize image for web (resize, compress, convert to WebP)."""
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
        
        if format.upper() == 'WEBP':
            save_kwargs['method'] = 6  # Best compression
        elif format.upper() == 'JPEG':
            save_kwargs['progressive'] = True
        elif format.upper() == 'PNG':
            save_kwargs['compress_level'] = 9
        
        image.save(output, **save_kwargs)
        optimized_bytes = output.getvalue()
        
        logger.info(f"Image optimized: {len(image_bytes)} -> {len(optimized_bytes)} bytes")
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

