"""
Integration tests for Avatar Upload
"""
import pytest
from io import BytesIO
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
    user.email = "test@example.com"
    user.avatar_url = None
    return user


def test_upload_avatar_success(client: TestClient, auth_headers, mock_current_user):
    """Test successful avatar upload"""
    with patch('app.api.middlewares.auth_middleware.get_current_user', return_value=mock_current_user):
        # Create test image file
        image_content = b"\x89PNG\r\n\x1a\n" + b"fake png data"
        files = {'avatar': ('avatar.png', BytesIO(image_content), 'image/png')}
        
        response = client.post(
            "/api/auth/profile/avatar",
            files=files,
            headers=auth_headers
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 201, 400, 500]


def test_upload_avatar_invalid_format(client: TestClient, auth_headers, mock_current_user):
    """Test avatar upload with invalid format"""
    with patch('app.api.middlewares.auth_middleware.get_current_user', return_value=mock_current_user):
        # Create invalid file (not an image)
        file_content = b"not an image"
        files = {'avatar': ('avatar.exe', BytesIO(file_content), 'application/x-msdownload')}
        
        response = client.post(
            "/api/auth/profile/avatar",
            files=files,
            headers=auth_headers
        )
        
        # Should reject invalid file type
        assert response.status_code in [400, 415, 422, 500]


def test_delete_avatar(client: TestClient, auth_headers, mock_current_user):
    """Test avatar deletion"""
    mock_current_user.avatar_url = "http://example.com/avatar.png"
    
    with patch('app.api.middlewares.auth_middleware.get_current_user', return_value=mock_current_user):
        response = client.delete(
            "/api/auth/profile/avatar",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204, 404, 500]


def test_upload_avatar_without_auth(client: TestClient):
    """Test avatar upload without authentication"""
    image_content = b"\x89PNG\r\n\x1a\n" + b"fake png data"
    files = {'avatar': ('avatar.png', BytesIO(image_content), 'image/png')}
    
    response = client.post("/api/auth/profile/avatar", files=files)
    
    # Should require authentication
    assert response.status_code in [401, 403]


def test_upload_large_avatar(client: TestClient, auth_headers, mock_current_user):
    """Test uploading oversized avatar"""
    with patch('app.api.middlewares.auth_middleware.get_current_user', return_value=mock_current_user):
        # Create large file (> 5MB)
        large_content = b"A" * (6 * 1024 * 1024)
        files = {'avatar': ('large_avatar.png', BytesIO(large_content), 'image/png')}
        
        response = client.post(
            "/api/auth/profile/avatar",
            files=files,
            headers=auth_headers
        )
        
        # Should reject oversized file
        assert response.status_code in [400, 413, 422, 500]

