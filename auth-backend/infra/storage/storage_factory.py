"""
Storage Factory
Creates storage provider instances based on configuration
"""
from core.interfaces.secondary import IFileStorage, StorageProvider
from .local_storage import LocalFileStorage
from .s3_storage import S3FileStorage
from .azure_storage import AzureBlobStorage
from .gcs_storage import GCSFileStorage
from .cloudinary_storage import CloudinaryStorage
from .cloudflare_images_storage import CloudflareImagesStorage
from .cdn_storage import CDNAwareStorage
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class StorageFactory:
    """
    Factory for creating storage provider instances.
    
    Uses settings to determine which provider to use.
    """
    
    @staticmethod
    def create_storage(provider: str = None) -> IFileStorage:
        """
        Create storage instance based on provider name.
        
        Args:
            provider: Storage provider name (local, s3, s3-cdn, azure, gcs, cloudinary, cloudflare)
                     If None, uses settings.storage_provider
        
        Returns:
            IFileStorage implementation
        
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider or getattr(settings, 'storage_provider', 'local')
        provider = provider.lower()
        
        if provider == StorageProvider.LOCAL or provider == 'local':
            logger.info("Using LOCAL file storage")
            return LocalFileStorage()
        
        elif provider == StorageProvider.S3 or provider == 's3':
            logger.info("Using AWS S3 file storage")
            return S3FileStorage()
        
        elif provider == 's3-cdn' or provider == 'cdn':
            logger.info("Using AWS S3 with CloudFront CDN")
            return CDNAwareStorage()
        
        elif provider == StorageProvider.AZURE or provider == 'azure':
            logger.info("Using Azure Blob Storage")
            return AzureBlobStorage()
        
        elif provider == StorageProvider.GCS or provider == 'gcs':
            logger.info("Using Google Cloud Storage")
            return GCSFileStorage()
        
        elif provider == StorageProvider.CLOUDINARY or provider == 'cloudinary':
            logger.info("Using Cloudinary")
            return CloudinaryStorage()
        
        elif provider == StorageProvider.CLOUDFLARE or provider == 'cloudflare':
            logger.info("Using Cloudflare Images")
            return CloudflareImagesStorage()
        
        else:
            raise ValueError(
                f"Unsupported storage provider: {provider}. "
                f"Supported: local, s3, s3-cdn, azure, gcs, cloudinary, cloudflare"
            )
    
    @staticmethod
    def get_default_storage() -> IFileStorage:
        """Get default storage provider from settings."""
        return StorageFactory.create_storage()

