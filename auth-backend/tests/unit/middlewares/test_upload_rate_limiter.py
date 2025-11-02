"""
Unit tests for Upload Rate Limiter Middleware
Tests file upload rate limiting logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from app.api.middlewares.upload_rate_limiter import UploadRateLimiter


@pytest.mark.unit
class TestUploadRateLimiter:
    """Test upload rate limiter functionality"""
    
    @pytest.mark.asyncio
    async def test_small_file_allowed(self):
        """Test small file uploads are allowed"""
        request_mock = Mock()
        request_mock.method = "POST"
        request_mock.url.path = "/api/files/upload"
        request_mock.headers = {"Content-Length": "1048576"}  # 1MB
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        limiter = UploadRateLimiter(Mock())
        
        response = await limiter.dispatch(request_mock, call_next_mock)
        
        assert response.status_code == 200
        call_next_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_exceeding_limit_rejected(self):
        """Test files exceeding size limit are rejected"""
        request_mock = Mock()
        request_mock.method = "POST"
        request_mock.url.path = "/api/files/upload"
        request_mock.headers = {"Content-Length": str(1024 * 1024 * 1024)}  # 1GB
        
        limiter = UploadRateLimiter(Mock())
        
        with pytest.raises(HTTPException) as exc_info:
            await limiter.dispatch(request_mock, AsyncMock())
        
        assert exc_info.value.status_code == 413  # Payload Too Large
    
    @pytest.mark.asyncio
    async def test_too_many_uploads_rate_limited(self):
        """Test too many uploads from same IP are rate limited"""
        request_mock = Mock()
        request_mock.method = "POST"
        request_mock.url.path = "/api/files/upload"
        request_mock.client.host = "1.2.3.4"
        request_mock.headers = {"Content-Length": "100000"}
        
        limiter = UploadRateLimiter(Mock())
        
        with patch('app.api.middlewares.upload_rate_limiter.check_upload_limit') as mock_check:
            mock_check.return_value = False  # Over limit
            
            with pytest.raises(HTTPException) as exc_info:
                await limiter.dispatch(request_mock, AsyncMock())
            
            assert exc_info.value.status_code == 429
    
    @pytest.mark.asyncio
    async def test_non_upload_requests_bypass(self):
        """Test non-upload requests bypass rate limiting"""
        request_mock = Mock()
        request_mock.method = "GET"
        request_mock.url.path = "/api/users"
        
        response_mock = Mock()
        response_mock.status_code = 200
        
        call_next_mock = AsyncMock(return_value=response_mock)
        
        limiter = UploadRateLimiter(Mock())
        
        response = await limiter.dispatch(request_mock, call_next_mock)
        
        assert response.status_code == 200

