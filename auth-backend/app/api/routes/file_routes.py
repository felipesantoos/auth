"""
File Upload & Management Routes
RESTful API endpoints for file operations
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Response
from typing import Optional
from core.interfaces.primary import IFileService
from app.api.dtos.response import (
    FileUploadResponse,
    FileInfoResponse,
    FileListResponse,
    PresignedUrlResponse,
    FileShareResponse
)
from app.api.middlewares.auth_middleware import get_current_user
from app.api.middlewares.upload_rate_limiter import upload_rate_limit
from app.api.dicontainer.dicontainer import get_file_service
from core.domain.auth.app_user import AppUser

router = APIRouter(prefix="/api/v1/files", tags=["File Upload"])


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
@upload_rate_limit(max_per_day=100, max_size_per_day_mb=1000)
async def upload_file(
    file: UploadFile = File(...),
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends(get_file_service)
):
    """
    Upload a file.
    
    - **file**: File to upload (multipart/form-data)
    - Returns: File metadata with URL
    """
    result = await file_service.upload_file(
        file=file,
        user_id=current_user.id,
        client_id=current_user.client_id or "",
        is_public=False
    )
    
    return FileUploadResponse(**result)


@router.get("", response_model=FileListResponse)
async def list_files(
    file_type: Optional[str] = Query(None, description="Filter by type: image, video, audio, document"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    List user's files with pagination.
    
    - **file_type**: Filter by file type (optional)
    - **page**: Page number (default: 1)
    - **per_page**: Results per page (default: 20, max: 100)
    """
    result = await file_service.list_user_files(
        user_id=current_user.id,
        file_type=file_type,
        page=page,
        per_page=per_page
    )
    
    return FileListResponse(**result)


@router.get("/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: str,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Get file information.
    
    - **file_id**: File ID
    - Returns: File metadata
    """
    result = await file_service.get_file_info(
        file_id=file_id,
        user_id=current_user.id
    )
    
    return FileInfoResponse(**result)


@router.head("/{file_id}")
async def check_file_exists(
    file_id: str,
    response: Response,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Check if file exists without returning body.
    
    Returns metadata headers:
    - Content-Type: File MIME type
    - Content-Length: File size in bytes
    - Last-Modified: When file was uploaded
    - ETag: File version hash
    
    HTTP Status:
    - 200 OK: File exists and user has access
    - 404 Not Found: File doesn't exist or no access
    
    Requires authentication.
    """
    from app.api.utils.cache_headers import add_last_modified_header, add_etag_header
    
    result = await file_service.get_file_info(
        file_id=file_id,
        user_id=current_user.id
    )
    
    # Add file-specific headers
    response.headers["Content-Type"] = result.get("content_type", "application/octet-stream")
    response.headers["Content-Length"] = str(result.get("size", 0))
    
    # Add cache headers
    if "updated_at" in result:
        from datetime import datetime
        updated_at = result["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        add_last_modified_header(response, updated_at)
    
    add_etag_header(response, result)
    
    return Response(status_code=200)


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Get download URL for file (with access control).
    
    - **file_id**: File ID
    - Returns: Signed URL (expires in 1 hour)
    """
    result = await file_service.download_file(
        file_id=file_id,
        user_id=current_user.id,
        generate_signed_url=True
    )
    
    return result


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Delete a file.
    
    - **file_id**: File ID
    - Only file owner can delete
    """
    await file_service.delete_file(
        file_id=file_id,
        user_id=current_user.id
    )
    
    return None


@router.post("/{file_id}/share", response_model=FileShareResponse)
async def share_file(
    file_id: str,
    share_with_user_id: str,
    permission: str = "read",
    expires_hours: Optional[int] = None,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Share file with another user.
    
    - **file_id**: File ID
    - **share_with_user_id**: User ID to share with
    - **permission**: Permission level (read, write)
    - **expires_hours**: Hours until share expires (optional)
    """
    result = await file_service.share_file(
        file_id=file_id,
        user_id=current_user.id,
        share_with_user_id=share_with_user_id,
        permission=permission,
        expires_hours=expires_hours
    )
    
    return FileShareResponse(**result)


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    filename: str,
    mime_type: str,
    file_size: int,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Get presigned URL for direct upload to S3.
    
    - **filename**: Original filename
    - **mime_type**: MIME type
    - **file_size**: File size in bytes
    - Returns: Presigned URL and upload fields
    """
    result = await file_service.get_presigned_upload_url(
        filename=filename,
        mime_type=mime_type,
        file_size=file_size,
        user_id=current_user.id,
        client_id=current_user.client_id or ""
    )
    
    return PresignedUrlResponse(**result)


@router.post("/complete-upload")
async def complete_direct_upload(
    upload_id: str,
    file_size: int,
    checksum: Optional[str] = None,
    current_user: AppUser = Depends(get_current_user),
    file_service: IFileService = Depends()
):
    """
    Complete direct upload (after uploading to presigned URL).
    
    - **upload_id**: Upload ID from presigned URL response
    - **file_size**: Final file size
    - **checksum**: Optional file checksum for verification
    """
    result = await file_service.complete_direct_upload(
        upload_id=upload_id,
        user_id=current_user.id,
        file_size=file_size,
        checksum=checksum
    )
    
    return result

