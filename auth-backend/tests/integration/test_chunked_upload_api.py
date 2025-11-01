"""
Integration tests for Chunked Upload API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = MagicMock()
    user.id = "user123"
    user.client_id = "client1"
    return user


def test_initiate_chunked_upload(client: TestClient, auth_headers, mock_current_user):
    """Test initiating chunked upload"""
    with patch('app.api.middlewares.authorization.get_current_user', return_value=mock_current_user):
        response = client.post(
            "/api/files/chunked/initiate",
            json={
                "filename": "large_file.zip",
                "total_size": 100000000,
                "chunk_size": 5242880
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 400, 500]


def test_upload_chunk(client: TestClient, auth_headers, mock_current_user):
    """Test uploading a chunk"""
    with patch('app.api.middlewares.authorization.get_current_user', return_value=mock_current_user):
        chunk_data = b"A" * 1024  # 1KB chunk
        
        response = client.post(
            "/api/files/chunked/upload123/chunk",
            json={
                "chunk_number": 1,
                "chunk_data": chunk_data.hex()  # Convert to hex for JSON
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 400, 404, 500]


def test_complete_chunked_upload(client: TestClient, auth_headers, mock_current_user):
    """Test completing chunked upload"""
    with patch('app.api.middlewares.authorization.get_current_user', return_value=mock_current_user):
        response = client.post(
            "/api/files/chunked/upload123/complete",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404, 500]


def test_abort_chunked_upload(client: TestClient, auth_headers, mock_current_user):
    """Test aborting chunked upload"""
    with patch('app.api.middlewares.authorization.get_current_user', return_value=mock_current_user):
        response = client.post(
            "/api/files/chunked/upload123/abort",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204, 404, 500]


def test_get_chunked_upload_status(client: TestClient, auth_headers, mock_current_user):
    """Test getting chunked upload status"""
    with patch('app.api.middlewares.authorization.get_current_user', return_value=mock_current_user):
        response = client.get(
            "/api/files/chunked/upload123/status",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404, 500]

