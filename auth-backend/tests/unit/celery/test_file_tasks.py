"""
Unit tests for Celery File Tasks
Tests file processing tasks without external dependencies
"""
import pytest
from infra.celery.tasks.file_tasks import process_uploaded_image, process_uploaded_video


@pytest.mark.unit
class TestFileTasks:
    """Test file Celery tasks"""
    
    def test_process_uploaded_image_task_exists(self):
        """Test processing uploaded image task exists"""
        assert callable(process_uploaded_image)
    
    def test_process_uploaded_video_task_exists(self):
        """Test processing uploaded video task exists"""
        assert callable(process_uploaded_video)
