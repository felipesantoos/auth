"""
Storage Factory
Creates storage provider instances based on configuration
"""
from core.interfaces.secondary import IFileStorage, StorageProvider
from .local_storage import LocalFileStorage
from .s3_storage import S3FileStorage
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
            provider: Storage provider name (local, s3, azure, gcs, cloudinary, cloudflare)
                     If None, uses settings.storage_provider
        
        Returns:
            IFileStorage implementation
        
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider or getattr(settings, 'storage_provider', 'local')
        provider = provider.lower()
        
        if provider == StorageProvider.LOCAL:
            logger.info("Using LOCAL file storage")
            return LocalFileStorage()
        
        elif provider == StorageProvider.S3:
            logger.info("Using AWS S3 file storage")
            return S3FileStorage()
        
        elif provider == StorageProvider.AZURE:
            # TODO: Implement Azure Blob Storage
            raise NotImplementedError("Azure Blob Storage not yet implemented")
        
        elif provider == StorageProvider.GCS:
            # TODO: Implement Google Cloud Storage
            raise NotImplementedError("Google Cloud Storage not yet implemented")
        
        elif provider == StorageProvider.CLOUDINARY:
            # TODO: Implement Cloudinary
            raise NotImplementedError("Cloudinary not yet implemented")
        
        elif provider == StorageProvider.CLOUDFLARE:
            # TODO: Implement Cloudflare Images
            raise NotImplementedError("Cloudflare Images not yet implemented")
        
        else:
            raise ValueError(
                f"Unsupported storage provider: {provider}. "
                f"Supported providers: {[p.value for p in StorageProvider]}"
            )
    
    @staticmethod
    def get_default_storage() -> IFileStorage:
        """Get default storage provider from settings."""
        return StorageFactory.create_storage()

