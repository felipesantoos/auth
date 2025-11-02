"""
Unit tests for AsyncTask domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime
from core.domain.task.async_task import AsyncTask, TaskStatus


@pytest.mark.unit
class TestTaskStatusEnum:
    """Test TaskStatus enum"""
    
    def test_pending_status_value(self):
        """Test PENDING status has correct value"""
        assert TaskStatus.PENDING.value == "pending"
    
    def test_processing_status_value(self):
        """Test PROCESSING status has correct value"""
        assert TaskStatus.PROCESSING.value == "processing"
    
    def test_completed_status_value(self):
        """Test COMPLETED status has correct value"""
        assert TaskStatus.COMPLETED.value == "completed"
    
    def test_failed_status_value(self):
        """Test FAILED status has correct value"""
        assert TaskStatus.FAILED.value == "failed"
    
    def test_cancelled_status_value(self):
        """Test CANCELLED status has correct value"""
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    def test_is_terminal_returns_true_for_completed(self):
        """Test is_terminal returns True for COMPLETED"""
        assert TaskStatus.COMPLETED.is_terminal() is True
    
    def test_is_terminal_returns_true_for_failed(self):
        """Test is_terminal returns True for FAILED"""
        assert TaskStatus.FAILED.is_terminal() is True
    
    def test_is_terminal_returns_true_for_cancelled(self):
        """Test is_terminal returns True for CANCELLED"""
        assert TaskStatus.CANCELLED.is_terminal() is True
    
    def test_is_terminal_returns_false_for_pending(self):
        """Test is_terminal returns False for PENDING"""
        assert TaskStatus.PENDING.is_terminal() is False
    
    def test_is_terminal_returns_false_for_processing(self):
        """Test is_terminal returns False for PROCESSING"""
        assert TaskStatus.PROCESSING.is_terminal() is False
    
    def test_is_active_returns_true_for_pending(self):
        """Test is_active returns True for PENDING"""
        assert TaskStatus.PENDING.is_active() is True
    
    def test_is_active_returns_true_for_processing(self):
        """Test is_active returns True for PROCESSING"""
        assert TaskStatus.PROCESSING.is_active() is True
    
    def test_is_active_returns_false_for_completed(self):
        """Test is_active returns False for COMPLETED"""
        assert TaskStatus.COMPLETED.is_active() is False


@pytest.mark.unit
class TestAsyncTaskCreation:
    """Test async task creation"""
    
    def test_create_task_with_minimal_data(self):
        """Test creating task with minimal data"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        assert task.task_type == "test_task"
        assert task.created_by == "user-123"
        assert task.client_id == "client-123"
        assert task.status == TaskStatus.PENDING
        assert task.id is not None
        assert task.created_at is not None
    
    def test_task_id_is_auto_generated(self):
        """Test task ID is auto-generated"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        assert task.id is not None
        assert len(task.id) > 0
    
    def test_task_created_at_is_set(self):
        """Test created_at is set on creation"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        assert task.created_at is not None
        assert isinstance(task.created_at, datetime)
    
    def test_task_defaults_to_pending_status(self):
        """Test task defaults to PENDING status"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        assert task.status == TaskStatus.PENDING
    
    def test_task_progress_defaults_to_zero(self):
        """Test task progress defaults to 0"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        assert task.progress_percentage == 0


@pytest.mark.unit
class TestAsyncTaskLifecycle:
    """Test task lifecycle methods"""
    
    def test_start_processing_changes_status_to_processing(self):
        """Test start_processing changes status to PROCESSING"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        task.start_processing()
        
        assert task.status == TaskStatus.PROCESSING
        assert task.started_at is not None
    
    def test_start_processing_only_works_from_pending(self):
        """Test start_processing only changes status from PENDING"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123",
            status=TaskStatus.COMPLETED
        )
        
        task.start_processing()
        
        # Status should not change
        assert task.status == TaskStatus.COMPLETED
    
    def test_complete_sets_status_and_result(self):
        """Test complete sets status to COMPLETED and saves result"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        result = {"success_count": 10, "failed_count": 0}
        task.complete(result)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.completed_at is not None
        assert task.progress_percentage == 100
    
    def test_fail_sets_status_and_error(self):
        """Test fail sets status to FAILED and saves error"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        error_message = "Something went wrong"
        task.fail(error_message)
        
        assert task.status == TaskStatus.FAILED
        assert task.error == error_message
        assert task.completed_at is not None
    
    def test_cancel_sets_status_to_cancelled(self):
        """Test cancel sets status to CANCELLED"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        task.cancel()
        
        assert task.status == TaskStatus.CANCELLED
        assert task.completed_at is not None
    
    def test_cancel_does_not_change_terminal_status(self):
        """Test cancel does not change terminal status"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123",
            status=TaskStatus.COMPLETED
        )
        
        task.cancel()
        
        # Status should not change
        assert task.status == TaskStatus.COMPLETED


@pytest.mark.unit
class TestAsyncTaskProgress:
    """Test task progress tracking"""
    
    def test_update_progress_sets_percentage(self):
        """Test update_progress sets progress percentage"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        task.update_progress(50)
        
        assert task.progress_percentage == 50
    
    def test_update_progress_sets_message(self):
        """Test update_progress sets progress message"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        task.update_progress(50, "Processing items...")
        
        assert task.progress_percentage == 50
        assert task.progress_message == "Processing items..."
    
    def test_update_progress_clamps_to_0_100(self):
        """Test update_progress clamps percentage to 0-100"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        task.update_progress(-10)
        assert task.progress_percentage == 0
        
        task.update_progress(150)
        assert task.progress_percentage == 100


@pytest.mark.unit
class TestAsyncTaskDuration:
    """Test task duration calculation"""
    
    def test_get_duration_seconds_returns_none_when_not_completed(self):
        """Test get_duration_seconds returns None when not completed"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        duration = task.get_duration_seconds()
        
        assert duration is None
    
    def test_get_duration_seconds_returns_duration_when_completed(self):
        """Test get_duration_seconds returns duration when completed"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        task.start_processing()
        task.complete({"success": True})
        
        duration = task.get_duration_seconds()
        
        assert duration is not None
        assert duration >= 0


@pytest.mark.unit
class TestAsyncTaskSerialization:
    """Test task serialization to dict"""
    
    def test_to_dict_contains_all_fields(self):
        """Test to_dict contains all expected fields"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123",
            payload={"data": "test"}
        )
        
        result_dict = task.to_dict()
        
        assert "id" in result_dict
        assert "task_type" in result_dict
        assert "status" in result_dict
        assert "payload" in result_dict
        assert "result" in result_dict
        assert "error" in result_dict
        assert "created_by" in result_dict
        assert "client_id" in result_dict
        assert "created_at" in result_dict
        assert "started_at" in result_dict
        assert "completed_at" in result_dict
        assert "progress_percentage" in result_dict
        assert "progress_message" in result_dict
        assert "duration_seconds" in result_dict
    
    def test_to_dict_serializes_datetime_to_iso_format(self):
        """Test to_dict serializes datetime to ISO format"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        result_dict = task.to_dict()
        
        assert isinstance(result_dict["created_at"], str)
        assert "T" in result_dict["created_at"]  # ISO format includes T
    
    def test_to_dict_serializes_status_to_value(self):
        """Test to_dict serializes status enum to value"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123"
        )
        
        result_dict = task.to_dict()
        
        assert result_dict["status"] == "pending"


@pytest.mark.unit
class TestAsyncTaskWithCelery:
    """Test task with Celery integration"""
    
    def test_task_can_have_celery_task_id(self):
        """Test task can have celery_task_id"""
        task = AsyncTask(
            task_type="test_task",
            created_by="user-123",
            client_id="client-123",
            celery_task_id="celery-task-123"
        )
        
        assert task.celery_task_id == "celery-task-123"


@pytest.mark.unit
class TestAsyncTaskWithPayload:
    """Test task with input payload"""
    
    def test_task_can_have_payload(self):
        """Test task can have input payload"""
        payload = {
            "users": [
                {"email": "user1@example.com"},
                {"email": "user2@example.com"}
            ]
        }
        
        task = AsyncTask(
            task_type="bulk_create_users",
            created_by="admin-123",
            client_id="client-123",
            payload=payload
        )
        
        assert task.payload == payload

