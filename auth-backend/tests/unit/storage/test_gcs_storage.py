"""
Unit tests for Google Cloud Storage
Tests GCS storage implementation without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.storage.gcs_storage import GCSFileStorage


@pytest.mark.unit
class TestGCSFileStorageInitialization:
    """Test GCS storage initialization"""

    @patch('google.cloud.storage.Client')
    @patch('infra.storage.gcs_storage.settings')
    def test_initializes_with_gcs_client(self, mock_settings, mock_gcs_client):
        """Should initialize with GCS client"""
        mock_settings.gcs_bucket_name = "test-bucket"
        mock_settings.gcs_project_id = "test-project"
        
        storage = GCSFileStorage()
        
        assert storage is not None
        assert hasattr(storage, 'bucket_name')

    @patch('google.cloud.storage.Client')
    @patch('infra.storage.gcs_storage.settings')
    def test_bucket_name_configured(self, mock_settings, mock_gcs_client):
        """Should configure bucket name from settings"""
        mock_settings.gcs_bucket_name = "my-gcs-bucket"
        mock_settings.gcs_project_id = "my-project"
        
        storage = GCSFileStorage()
        
        assert storage.bucket_name == "my-gcs-bucket"


@pytest.mark.unit
class TestGCSFileStorageMethods:
    """Test GCS storage methods exist"""

    @patch('google.cloud.storage.Client')
    @patch('infra.storage.gcs_storage.settings')
    def test_has_upload_file_method(self, mock_settings, mock_gcs_client):
        """Should have upload_file method"""
        mock_settings.gcs_bucket_name = "test-bucket"
        mock_settings.gcs_project_id = "test-project"
        
        storage = GCSFileStorage()
        
        assert hasattr(storage, 'upload_file')
        assert callable(storage.upload_file)

    @patch('google.cloud.storage.Client')
    @patch('infra.storage.gcs_storage.settings')
    def test_has_download_file_method(self, mock_settings, mock_gcs_client):
        """Should have download_file method"""
        mock_settings.gcs_bucket_name = "test-bucket"
        mock_settings.gcs_project_id = "test-project"
        
        storage = GCSFileStorage()
        
        assert hasattr(storage, 'download_file')
        assert callable(storage.download_file)

    @patch('google.cloud.storage.Client')
    @patch('infra.storage.gcs_storage.settings')
    def test_has_delete_file_method(self, mock_settings, mock_gcs_client):
        """Should have delete_file method"""
        mock_settings.gcs_bucket_name = "test-bucket"
        mock_settings.gcs_project_id = "test-project"
        
        storage = GCSFileStorage()
        
        assert hasattr(storage, 'delete_file')
        assert callable(storage.delete_file)

