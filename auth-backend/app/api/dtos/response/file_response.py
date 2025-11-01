"""File Response DTOs"""
from pydantic import BaseModel
from typing import List, Optional


class FileUploadResponse(BaseModel):
    """Response for file upload"""
    id: str
    filename: str
    url: str
    size: int
    mime_type: str
    checksum: str
    duplicate: bool = False


class FileInfoResponse(BaseModel):
    """Response for file information"""
    id: str
    filename: str
    url: str
    size: int
    mime_type: str
    checksum: str
    is_public: bool
    tags: List[str]
    uploaded_at: Optional[str] = None


class FileListItemResponse(BaseModel):
    """Single file item in list"""
    id: str
    filename: str
    url: str
    size: int
    mime_type: str
    uploaded_at: Optional[str] = None


class PaginationResponse(BaseModel):
    """Pagination metadata"""
    page: int
    per_page: int
    total: int
    total_pages: int


class FileListResponse(BaseModel):
    """Response for file list"""
    data: List[FileListItemResponse]
    pagination: PaginationResponse


class PresignedUrlResponse(BaseModel):
    """Response for presigned URL"""
    url: str
    fields: dict
    file_path: str
    file_id: str
    expires_in: int


class FileShareResponse(BaseModel):
    """Response for file share"""
    share_id: str
    file_id: str
    shared_with: str
    permission: str
    expires_at: Optional[str] = None

