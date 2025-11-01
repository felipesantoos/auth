"""
Serve Files Routes
Serves uploaded files with security headers (for local storage)
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pathlib import Path
import os
import mimetypes
from config.settings import settings

router = APIRouter(prefix="/uploads", tags=["Static Files"])


@router.get("/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve uploaded file from local storage.
    
    Security headers applied:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Content-Security-Policy: restricted
    
    Note: In production, serve files from CDN/S3 instead.
    """
    # Build full path
    base_path = getattr(settings, 'local_storage_path', 'uploads')
    full_path = Path(base_path) / file_path
    
    # Security: Prevent path traversal
    try:
        full_path = full_path.resolve()
        base_path_resolved = Path(base_path).resolve()
        
        if not str(full_path).startswith(str(base_path_resolved)):
            raise HTTPException(403, "Access denied")
    except:
        raise HTTPException(403, "Invalid path")
    
    # Check if file exists
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(404, "File not found")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(full_path))
    mime_type = mime_type or 'application/octet-stream'
    
    # Security headers
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline';",
        "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
    }
    
    # Force download for potentially dangerous types
    dangerous_types = [
        'application/x-executable',
        'application/x-ms-dos-executable',
        'application/x-sh',
        'text/html'  # Prevent HTML execution
    ]
    
    if mime_type in dangerous_types:
        headers["Content-Disposition"] = f'attachment; filename="{full_path.name}"'
    else:
        headers["Content-Disposition"] = f'inline; filename="{full_path.name}"'
    
    return FileResponse(
        path=str(full_path),
        media_type=mime_type,
        headers=headers
    )

