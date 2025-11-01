"""
File Service Interface (Primary Port)
Defines the contract for file management operations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from fastapi import UploadFile


class IFileService(ABC):
    """
    File service interface (primary port).
    
    Defines business operations for file management.
    """
    
    @abstractmethod
    async def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        client_id: str,
        directory: str = "uploads",
        is_public: bool = False,
        tags: List[str] = None
    ) -> Dict:
        """
        Upload file with validation and storage.
        
        Args:
            file: Upload file from request
            user_id: ID of user uploading
            client_id: Client ID for multi-tenant
            directory: Directory to store file
            is_public: Whether file should be publicly accessible
            tags: Optional tags for the file
            
        Returns:
            Dict with file information
        """
        pass
    
    @abstractmethod
    async def download_file(
        self,
        file_id: str,
        user_id: str,
        generate_signed_url: bool = True
    ) -> Dict:
        """
        Download file with access control.
        
        Args:
            file_id: File ID
            user_id: ID of user requesting download
            generate_signed_url: Whether to generate signed URL
            
        Returns:
            Dict with file URL or file content
        """
        pass
    
    @abstractmethod
    async def delete_file(
        self,
        file_id: str,
        user_id: str
    ) -> bool:
        """
        Delete file with ownership check.
        
        Args:
            file_id: File ID
            user_id: ID of user requesting deletion
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def get_file_info(
        self,
        file_id: str,
        user_id: str
    ) -> Dict:
        """
        Get file information with access control.
        
        Args:
            file_id: File ID
            user_id: ID of user requesting info
            
        Returns:
            Dict with file metadata
        """
        pass
    
    @abstractmethod
    async def list_user_files(
        self,
        user_id: str,
        file_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """
        List files owned by user.
        
        Args:
            user_id: User ID
            file_type: Filter by type (image, video, document, audio)
            page: Page number
            per_page: Results per page
            
        Returns:
            Dict with paginated file list
        """
        pass
    
    @abstractmethod
    async def update_file_metadata(
        self,
        file_id: str,
        user_id: str,
        filename: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None
    ) -> Dict:
        """
        Update file metadata.
        
        Args:
            file_id: File ID
            user_id: ID of user updating
            filename: New filename
            tags: New tags
            is_public: New public status
            
        Returns:
            Dict with updated file info
        """
        pass
    
    @abstractmethod
    async def share_file(
        self,
        file_id: str,
        user_id: str,
        share_with_user_id: str,
        permission: str = "read",
        expires_hours: Optional[int] = None
    ) -> Dict:
        """
        Share file with another user.
        
        Args:
            file_id: File ID
            user_id: ID of file owner
            share_with_user_id: ID of user to share with
            permission: Permission level (read, write)
            expires_hours: Hours until expiration (None = never)
            
        Returns:
            Dict with share information
        """
        pass
    
    @abstractmethod
    async def revoke_share(
        self,
        share_id: str,
        user_id: str
    ) -> bool:
        """
        Revoke file share.
        
        Args:
            share_id: Share ID
            user_id: ID of file owner
            
        Returns:
            True if revoked successfully
        """
        pass
    
    @abstractmethod
    async def get_presigned_upload_url(
        self,
        filename: str,
        mime_type: str,
        file_size: int,
        user_id: str,
        client_id: str
    ) -> Dict:
        """
        Generate presigned URL for direct upload.
        
        Args:
            filename: Original filename
            mime_type: MIME type
            file_size: File size in bytes
            user_id: User ID
            client_id: Client ID
            
        Returns:
            Dict with presigned URL and upload fields
        """
        pass
    
    @abstractmethod
    async def complete_direct_upload(
        self,
        upload_id: str,
        user_id: str,
        file_size: int,
        checksum: Optional[str] = None
    ) -> Dict:
        """
        Complete direct upload flow.
        
        Args:
            upload_id: Upload ID from presigned URL
            user_id: User ID
            file_size: Final file size
            checksum: Optional checksum for verification
            
        Returns:
            Dict with completed file info
        """
        pass

