"""
Unit tests for ImageProcessor
"""
import pytest
from io import BytesIO
from PIL import Image
from infra.storage.image_processor import ImageProcessor


@pytest.fixture
def processor():
    """Create ImageProcessor instance"""
    return ImageProcessor()


@pytest.fixture
def create_test_image():
    """Helper to create test images"""
    def _create(width=800, height=600, color=(255, 0, 0), format='PNG'):
        img = Image.new('RGB', (width, height), color)
        buffer = BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer
    return _create


@pytest.mark.asyncio
async def test_optimize_image(processor, create_test_image):
    """Test image optimization"""
    image_bytes = create_test_image(width=1000, height=800).read()
    
    optimized = await processor.optimize_image(image_bytes, quality=80)
    
    assert len(optimized) > 0
    assert len(optimized) <= len(image_bytes)  # Should be smaller or equal
    
    # Verify it's still a valid image
    img = Image.open(BytesIO(optimized))
    assert img.format in ['JPEG', 'PNG', 'WEBP']


@pytest.mark.asyncio
async def test_create_thumbnail(processor, create_test_image):
    """Test thumbnail creation"""
    image_bytes = create_test_image(width=1000, height=800).read()
    
    thumbnail = await processor.create_thumbnails(image_bytes, size=(200, 200))
    
    assert len(thumbnail) > 0
    
    # Verify thumbnail dimensions
    img = Image.open(BytesIO(thumbnail))
    assert img.width <= 200
    assert img.height <= 200


@pytest.mark.asyncio
async def test_create_responsive_images(processor, create_test_image):
    """Test creating multiple responsive sizes"""
    image_bytes = create_test_image(width=2000, height=1500).read()
    
    sizes = [(400, 300), (800, 600), (1200, 900)]
    responsive_images = await processor.create_responsive_images(image_bytes, sizes)
    
    assert len(responsive_images) == 3
    
    for size_name, image_data in responsive_images.items():
        assert len(image_data) > 0
        img = Image.open(BytesIO(image_data))
        assert img.width <= sizes[list(responsive_images.keys()).index(size_name)][0]


@pytest.mark.asyncio
async def test_resize_image(processor, create_test_image):
    """Test image resizing"""
    image_bytes = create_test_image(width=1000, height=800).read()
    
    resized = await processor.resize_image(image_bytes, width=500, height=400)
    
    img = Image.open(BytesIO(resized))
    assert img.width == 500
    assert img.height == 400


@pytest.mark.asyncio
async def test_convert_format(processor, create_test_image):
    """Test image format conversion"""
    png_bytes = create_test_image(format='PNG').read()
    
    jpeg_bytes = await processor.convert_format(png_bytes, target_format='JPEG')
    
    img = Image.open(BytesIO(jpeg_bytes))
    assert img.format == 'JPEG'


@pytest.mark.asyncio
async def test_extract_dominant_color(processor, create_test_image):
    """Test dominant color extraction"""
    # Create image with known color
    image_bytes = create_test_image(color=(255, 0, 0)).read()  # Red
    
    dominant_color = await processor.extract_dominant_colors(image_bytes)
    
    assert isinstance(dominant_color, tuple)
    assert len(dominant_color) == 3
    assert all(0 <= c <= 255 for c in dominant_color)
    # Should be reddish (R > G and R > B)
    assert dominant_color[0] > dominant_color[1]
    assert dominant_color[0] > dominant_color[2]


@pytest.mark.asyncio
async def test_get_image_metadata(processor, create_test_image):
    """Test image metadata extraction"""
    image_bytes = create_test_image(width=1000, height=800).read()
    
    metadata = await processor.get_image_metadata(image_bytes)
    
    assert metadata['width'] == 1000
    assert metadata['height'] == 800
    assert metadata['format'] in ['PNG', 'JPEG']
    assert metadata['mode'] in ['RGB', 'RGBA']
    assert 'size_bytes' in metadata


@pytest.mark.asyncio
async def test_crop_image(processor, create_test_image):
    """Test image cropping"""
    image_bytes = create_test_image(width=1000, height=800).read()
    
    cropped = await processor.crop_image(
        image_bytes,
        left=100,
        top=100,
        right=600,
        bottom=500
    )
    
    img = Image.open(BytesIO(cropped))
    assert img.width == 500  # 600 - 100
    assert img.height == 400  # 500 - 100


@pytest.mark.asyncio
async def test_add_watermark(processor, create_test_image):
    """Test adding text watermark"""
    image_bytes = create_test_image(width=1000, height=800).read()
    
    watermarked = await processor.add_watermark(
        image_bytes,
        text="© Test Watermark",
        position="bottom-right",
        opacity=128
    )
    
    assert len(watermarked) > 0
    
    # Verify it's still a valid image
    img = Image.open(BytesIO(watermarked))
    assert img.width == 1000
    assert img.height == 800

