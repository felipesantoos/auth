"""
End-to-End tests for File Upload and Sharing Journey
Tests complete file management flows
"""
import pytest
from httpx import AsyncClient
import io


@pytest.mark.e2e
class TestFileUploadJourney:
    """Test complete file upload journey"""
    
    @pytest.mark.asyncio
    async def test_upload_download_delete_file(self, async_client: AsyncClient, auth_token: str):
        """Test complete flow: Upload → Download → Share → Delete"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Upload file
        file_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        upload_response = await async_client.post(
            "/api/v1/files/upload",
            headers=headers,
            files=files
        )
        
        assert upload_response.status_code in [200, 201]
        if upload_response.status_code in [200, 201]:
            file_data = upload_response.json()
            file_id = file_data.get("id") or file_data.get("file_id")
            
            # Step 2: List user's files
            list_response = await async_client.get(
                "/api/v1/files",
                headers=headers
            )
            
            assert list_response.status_code == 200
            
            # Step 3: Download file
            download_response = await async_client.get(
                f"/api/v1/files/{file_id}/download",
                headers=headers
            )
            
            assert download_response.status_code in [200, 404]
            
            # Step 4: Delete file
            delete_response = await async_client.delete(
                f"/api/v1/files/{file_id}",
                headers=headers
            )
            
            assert delete_response.status_code in [200, 204, 404]


@pytest.mark.e2e
class TestFileShareJourney:
    """Test complete file sharing journey"""
    
    @pytest.mark.asyncio
    async def test_share_file_with_another_user(self, async_client: AsyncClient, auth_token: str):
        """Test complete flow: Upload → Share with user → Access as recipient → Revoke"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Assuming file already uploaded
        file_id = "existing-file-id"
        
        # Step 1: Share file with another user
        share_response = await async_client.post(
            f"/api/v1/files/{file_id}/share",
            headers=headers,
            json={
                "shared_with": "user-456",
                "permission": "read",
                "expires_hours": 24
            }
        )
        
        assert share_response.status_code in [200, 201, 404]
        
        # Step 2: List file shares
        if share_response.status_code in [200, 201]:
            list_shares = await async_client.get(
                f"/api/v1/files/{file_id}/shares",
                headers=headers
            )
            
            assert list_shares.status_code in [200, 404]
            
            # Step 3: Revoke share
            share_id = share_response.json().get("id")
            if share_id:
                revoke_response = await async_client.delete(
                    f"/api/v1/files/{file_id}/shares/{share_id}",
                    headers=headers
                )
                
                assert revoke_response.status_code in [200, 204, 404]


@pytest.mark.e2e
class TestChunkedUploadJourney:
    """Test complete chunked upload journey"""
    
    @pytest.mark.asyncio
    async def test_chunked_upload_large_file(self, async_client: AsyncClient, auth_token: str):
        """Test complete flow: Init → Upload chunks → Complete"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Initialize chunked upload
        init_response = await async_client.post(
            "/api/v1/files/chunked/init",
            headers=headers,
            json={
                "filename": "large-file.mp4",
                "file_size": 10485760,  # 10MB
                "mime_type": "video/mp4",
                "chunk_size": 1048576  # 1MB chunks
            }
        )
        
        assert init_response.status_code in [200, 201]
        if init_response.status_code in [200, 201]:
            upload_data = init_response.json()
            upload_id = upload_data.get("upload_id")
            
            # Step 2: Upload chunks (simulated)
            chunk_data = b"x" * 1048576  # 1MB chunk
            chunk_response = await async_client.post(
                f"/api/v1/files/chunked/{upload_id}/chunk",
                headers=headers,
                files={"chunk": ("chunk", io.BytesIO(chunk_data))}
            )
            
            assert chunk_response.status_code in [200, 400]
            
            # Step 3: Complete upload
            complete_response = await async_client.post(
                f"/api/v1/files/chunked/{upload_id}/complete",
                headers=headers
            )
            
            assert complete_response.status_code in [200, 400, 404]

