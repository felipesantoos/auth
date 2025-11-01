"""Storage implementations package"""
from .local_storage import LocalFileStorage
from .s3_storage import S3FileStorage
from .azure_storage import AzureBlobStorage
from .gcs_storage import GCSFileStorage
from .cloudinary_storage import CloudinaryStorage
from .cloudflare_images_storage import CloudflareImagesStorage
from .cdn_storage import CDNAwareStorage
from .storage_factory import StorageFactory
from .image_processor import ImageProcessor

__all__ = [
    "LocalFileStorage",
    "S3FileStorage",
    "AzureBlobStorage",
    "GCSFileStorage",
    "CloudinaryStorage",
    "CloudflareImagesStorage",
    "CDNAwareStorage",
    "StorageFactory",
    "ImageProcessor",
]

