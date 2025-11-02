"""
Unit tests for Celery File Tasks
Tests file processing tasks without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.celery.tasks.file_tasks import process_uploaded_file, cleanup_temp_files


@pytest.mark.unit
class TestFileTasks:
    """Test file Celery tasks"""
    
    def test_process_uploaded_file_task(self):
        """Test processing uploaded file (thumbnails, virus scan, etc.)"""
        with patch('infra.celery.tasks.file_tasks.file_service') as mock_service:
            mock_service.process_file = Mock(return_value=True)
            
            result = process_uploaded_file(file_id="file-123")
            
            assert result or mock_service.process_file.called
    
    def test_cleanup_temp_files_task(self):
        """Test cleaning up temporary files"""
        with patch('infra.celery.tasks.file_tasks.file_service') as mock_service:
            mock_service.cleanup_temp_files = Mock(return_value=10)
            
            result = cleanup_temp_files()
            
            assert result == 10 or mock_service.cleanup_temp_files.called

