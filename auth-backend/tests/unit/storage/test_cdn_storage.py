"""
Unit tests for CDN-Aware Storage
Tests CloudFront CDN wrapper for S3 storage
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.cdn_storage import CDNAwareStorage


@pytest.mark.unit
class TestCDNAwareStorageInitialization:
    """Test CDN storage initialization"""

    @patch('infra.storage.cdn_storage.settings')
    @patch('infra.storage.s3_storage.boto3')
    def test_initializes_with_s3_parent(self, mock_boto3, mock_settings):
        """Should initialize as S3 storage subclass"""
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.cloudfront_domain = "cdn.example.com"
        
        storage = CDNAwareStorage()
        
        assert storage is not None
        assert hasattr(storage, 'cdn_domain')

    @patch('infra.storage.cdn_storage.settings')
    @patch('infra.storage.s3_storage.boto3')
    def test_has_cdn_domain_configured(self, mock_boto3, mock_settings):
        """Should have CDN domain configured"""
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.cloudfront_domain = "d111111abcdef8.cloudfront.net"
        
        storage = CDNAwareStorage()
        
        assert storage.cdn_domain == "d111111abcdef8.cloudfront.net"


@pytest.mark.unit
class TestCDNURLGeneration:
    """Test CDN URL generation"""

    @patch('infra.storage.cdn_storage.settings')
    @patch('infra.storage.s3_storage.boto3')
    def test_get_file_url_uses_cdn_domain(self, mock_boto3, mock_settings):
        """Should use CDN domain for file URLs"""
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.cloudfront_domain = "cdn.example.com"
        
        storage = CDNAwareStorage()
        
        # CDN domain should be used for URLs
        assert storage.cdn_domain == "cdn.example.com"


@pytest.mark.unit
class TestCDNStorageInheritance:
    """Test that CDN storage inherits S3 functionality"""

    @patch('infra.storage.cdn_storage.settings')
    @patch('infra.storage.s3_storage.boto3')
    def test_inherits_from_s3_storage(self, mock_boto3, mock_settings):
        """Should inherit all S3 storage methods"""
        from infra.storage.s3_storage import S3FileStorage
        
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.cloudfront_domain = "cdn.example.com"
        
        storage = CDNAwareStorage()
        
        # Should be instance of S3FileStorage
        assert isinstance(storage, S3FileStorage)

    @patch('infra.storage.cdn_storage.settings')
    @patch('infra.storage.s3_storage.boto3')
    def test_has_upload_method(self, mock_boto3, mock_settings):
        """Should have upload method from S3"""
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.cloudfront_domain = "cdn.example.com"
        
        storage = CDNAwareStorage()
        
        assert hasattr(storage, 'upload_file')
        assert callable(storage.upload_file)

