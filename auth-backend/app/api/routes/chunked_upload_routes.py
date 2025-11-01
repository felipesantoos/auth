"""
Chunked Upload Routes
API endpoints for multipart/chunked uploads
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from core.services.files.chunked_upload_manager import ChunkedUploadManager
from app.api.middlewares.authorization import get_current_user
from app.api.dicontainer.dicontainer import get_chunked_upload_manager
from core.domain.auth.app_user import AppUser
from pydantic import BaseModel

router = APIRouter(prefix="/api/upload/chunked", tags=["Chunked Upload"])


class InitChunkedUploadRequest(BaseModel):
    """Request to initiate chunked upload"""
    filename: str
    mime_type: str
    total_size: int


class UploadChunkResponse(BaseModel):
    """Response for chunk upload"""
    part_number: int
    etag: str
    uploaded: int


class CompleteUploadResponse(BaseModel):
    """Response for completed upload"""
    id: str
    url: str
    size: int


@router.post("/init")
async def init_chunked_upload(
    request: InitChunkedUploadRequest,
    current_user: AppUser = Depends(get_current_user),
    chunked_manager: ChunkedUploadManager = Depends(get_chunked_upload_manager)
):
    """
    Initialize chunked upload.
    
    - **filename**: Original filename
    - **mime_type**: MIME type
    - **total_size**: Total file size in bytes
    - Returns: Upload ID and chunk size
    """
    return await chunked_manager.initiate_multipart_upload(
        filename=request.filename,
        mime_type=request.mime_type,
        user_id=current_user.id
    )


@router.post("/{upload_id}/chunk", response_model=UploadChunkResponse)
async def upload_chunk(
    upload_id: str,
    chunk_number: int,
    chunk: UploadFile = File(...),
    current_user: AppUser = Depends(get_current_user),
    chunked_manager: ChunkedUploadManager = Depends()
):
    """
    Upload a chunk.
    
    - **upload_id**: Upload ID from init response
    - **chunk_number**: Part number (1-indexed)
    - **chunk**: Chunk data (multipart/form-data)
    - Returns: Chunk metadata
    """
    chunk_data = await chunk.read()
    
    return await chunked_manager.upload_chunk(
        upload_id=upload_id,
        chunk_number=chunk_number,
        chunk_data=chunk_data
    )


@router.post("/{upload_id}/complete", response_model=CompleteUploadResponse)
async def complete_chunked_upload(
    upload_id: str,
    current_user: AppUser = Depends(get_current_user),
    chunked_manager: ChunkedUploadManager = Depends()
):
    """
    Complete chunked upload.
    
    - **upload_id**: Upload ID
    - Returns: File metadata with URL
    """
    uploaded_file = await chunked_manager.complete_multipart_upload(upload_id)
    
    # Get file URL from storage
    from infra.storage.storage_factory import StorageFactory
    storage = StorageFactory.get_default_storage()
    
    url = await storage.get_file_url(uploaded_file.file_path)
    
    return CompleteUploadResponse(
        id=uploaded_file.id,
        url=url,
        size=uploaded_file.file_size
    )


@router.delete("/{upload_id}/abort")
async def abort_chunked_upload(
    upload_id: str,
    current_user: AppUser = Depends(get_current_user),
    chunked_manager: ChunkedUploadManager = Depends()
):
    """
    Abort chunked upload.
    
    - **upload_id**: Upload ID
    - Returns: Success status
    """
    success = await chunked_manager.abort_multipart_upload(upload_id)
    
    if not success:
        raise HTTPException(404, "Upload not found")
    
    return {"status": "aborted", "upload_id": upload_id}

