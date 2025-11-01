"""
CDN-Aware Storage Implementation
Wrapper for S3 Storage with CloudFront CDN support
"""
from typing import BinaryIO, Dict, List
from core.interfaces.secondary import IFileStorage, UploadedFile
from .s3_storage import S3FileStorage
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class CDNAwareStorage(S3FileStorage):
    """
    S3 storage with CloudFront CDN support.
    
    Features:
    - Uses S3 for storage
    - Serves files via CloudFront CDN for better performance
    - Signed CloudFront URLs for private files
    - Lower latency and data transfer costs
    """
    
    def __init__(self):
        """Initialize with S3 + CloudFront config."""
        super().__init__()
        self.cdn_domain = settings.cloudfront_domain
        self.cloudfront_key_id = settings.cloudfront_key_id
        self.cloudfront_private_key_path = settings.cloudfront_private_key
    
    async def get_file_url(
        self,
        file_path: str,
        expiration: int = None,
        use_cdn: bool = True
    ) -> str:
        """
        Get file URL (via CDN if available).
        
        Args:
            file_path: S3 key
            expiration: Seconds until expiration (for signed URLs)
            use_cdn: Whether to use CDN (default: True)
        
        Returns:
            CDN URL or S3 URL
        """
        if not use_cdn or not self.cdn_domain:
            # Fallback to S3 URL
            return await super().get_file_url(file_path, expiration)
        
        base_url = f"https://{self.cdn_domain}"
        file_url = f"{base_url}/{file_path}"
        
        if expiration and self.cloudfront_key_id and self.cloudfront_private_key_path:
            # Generate signed CloudFront URL
            try:
                return self._get_signed_cloudfront_url(file_url, expiration)
            except Exception as e:
                logger.error(f"Failed to generate CloudFront signed URL: {e}")
                # Fallback to S3 signed URL
                return await super().get_file_url(file_path, expiration)
        else:
            # Public CDN URL
            return file_url
    
    def _get_signed_cloudfront_url(self, url: str, expiration: int) -> str:
        """
        Generate signed CloudFront URL.
        
        Args:
            url: CloudFront URL to sign
            expiration: Seconds until expiration
        
        Returns:
            Signed CloudFront URL
        """
        try:
            from botocore.signers import CloudFrontSigner
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend
            import time
            
            # Load private key
            with open(self.cloudfront_private_key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            
            # Create signer function
            def rsa_signer(message):
                return private_key.sign(
                    message,
                    padding.PKCS1v15(),
                    hashes.SHA1()
                )
            
            # Create CloudFront signer
            cloudfront_signer = CloudFrontSigner(
                self.cloudfront_key_id,
                rsa_signer
            )
            
            # Generate signed URL
            expire_time = int(time.time()) + expiration
            
            signed_url = cloudfront_signer.generate_presigned_url(
                url,
                date_less_than=expire_time
            )
            
            return signed_url
        
        except Exception as e:
            logger.error(f"CloudFront signing failed: {e}", exc_info=True)
            raise

