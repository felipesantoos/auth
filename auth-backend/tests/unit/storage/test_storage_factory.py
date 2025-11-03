"""
Unit tests for Storage Factory
Tests storage provider factory logic without external dependencies
"""
import pytest
from unittest.mock import Mock, patch
from infra.storage.storage_factory import StorageFactory


@pytest.mark.unit
class TestStorageFactory:
    """Test storage factory functionality"""
    
    def test_get_storage_returns_local_storage(self):
        """Test factory returns local storage for local provider"""
        settings_mock = Mock()
        settings_mock.storage_provider = "local"
        settings_mock.local_storage_path = "/tmp/uploads"
        
        with patch('infra.storage.storage_factory.settings', settings_mock):
            storage = StorageFactory.create_storage()
            
            assert storage is not None
    
    def test_get_storage_returns_s3_storage(self):
        """Test factory returns S3 storage for s3 provider"""
        settings_mock = Mock()
        settings_mock.storage_provider = "s3"
        settings_mock.aws_access_key_id = "key"
        settings_mock.aws_secret_access_key = "secret"
        settings_mock.aws_s3_bucket = "bucket"
        
        with patch('infra.storage.storage_factory.settings', settings_mock):
            storage = StorageFactory.create_storage()
            
            assert storage is not None
    
    def test_get_storage_returns_gcs_storage(self):
        """Test factory returns GCS storage for gcs provider"""
        settings_mock = Mock()
        settings_mock.storage_provider = "gcs"
        settings_mock.gcs_bucket_name = "bucket"
        
        with patch('infra.storage.storage_factory.settings', settings_mock):
            with patch('google.cloud.storage.Client'):
                storage = StorageFactory.create_storage()
                
                assert storage is not None

