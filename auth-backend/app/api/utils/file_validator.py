"""
Comprehensive File Validator
Security-focused validation for file uploads
"""
import re
import hashlib
from fastapi import UploadFile, HTTPException
from typing import Dict, List, Set
from io import BytesIO
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Comprehensive file validation for security.
    
    Validates:
    - File size
    - File extension (blocked dangerous extensions)
    - MIME type (using python-magic if available, fallback to content-type)
    - Magic numbers (file signatures)
    - Filename safety
    - Image-specific validation (dimensions, decompression bomb)
    - Optional: Malware scanning (ClamAV)
    """
    
    def __init__(self):
        self.max_size = getattr(settings, 'file_upload_max_size', 100 * 1024 * 1024)  # 100MB default
        self.allowed_types = set(getattr(settings, 'allowed_file_types', [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'video/mp4', 'audio/mpeg'
        ]))
        
        # Dangerous file extensions (always blocked)
        self.blocked_extensions = {
            'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js',
            'jar', 'sh', 'ps1', 'app', 'deb', 'rpm', 'msi', 'dll'
        }
        
        # Magic number signatures for common files
        self.magic_numbers = {
            'image/jpeg': [b'\xFF\xD8\xFF'],
            'image/png': [b'\x89PNG\r\n\x1a\n'],
            'image/gif': [b'GIF87a', b'GIF89a'],
            'image/webp': [b'RIFF'],
            'application/pdf': [b'%PDF-'],
            'video/mp4': [b'\x00\x00\x00\x18ftypmp4', b'\x00\x00\x00\x1cftypisom'],
        }
    
    async def validate_file(self, file: UploadFile) -> Dict:
        """
        Validate file comprehensively.
        
        Returns:
            {
                "valid": bool,
                "file_size": int,
                "mime_type": str,
                "checksum": str,
                "extension": str,
                "errors": List[str]
            }
        """
        errors = []
        
        # Read file content once
        content = await file.read()
        await file.seek(0)  # Reset for potential re-reading
        file_size = len(content)
        
        # 1. Size validation
        if file_size == 0:
            errors.append("File is empty")
        elif file_size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            errors.append(f"File too large. Maximum size is {max_mb:.1f}MB")
        
        # 2. Extension validation
        extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if extension in self.blocked_extensions:
            errors.append(f"File extension '.{extension}' is blocked for security reasons")
        
        # 3. MIME type detection
        detected_mime = self._detect_mime_type(content, file.content_type)
        
        if self.allowed_types and detected_mime not in self.allowed_types:
            errors.append(f"File type '{detected_mime}' is not allowed")
        
        # 4. Magic number validation (verify file signature)
        if detected_mime in self.magic_numbers:
            signatures = self.magic_numbers[detected_mime]
            if not any(content.startswith(sig) for sig in signatures):
                errors.append("File signature doesn't match declared type (possible spoofing)")
        
        # 5. Filename validation
        if not self._is_safe_filename(file.filename):
            errors.append("Filename contains invalid characters")
        
        # 6. Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # 7. Image-specific validation
        if detected_mime.startswith('image/'):
            image_errors = await self._validate_image(content)
            errors.extend(image_errors)
        
        return {
            "valid": len(errors) == 0,
            "file_size": file_size,
            "mime_type": detected_mime,
            "checksum": checksum,
            "extension": extension,
            "errors": errors
        }
    
    def _detect_mime_type(self, content: bytes, declared_type: str) -> str:
        """
        Detect MIME type from content.
        
        Try python-magic if available, otherwise use declared type.
        """
        try:
            import magic
            mime = magic.Magic(mime=True)
            return mime.from_buffer(content)
        except ImportError:
            # Fallback to declared content type if magic not available
            logger.warning("python-magic not available, using declared content-type")
            return declared_type or 'application/octet-stream'
        except Exception as e:
            logger.error(f"MIME detection failed: {e}")
            return declared_type or 'application/octet-stream'
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe (no path traversal, etc)."""
        # No path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # No null bytes
        if '\x00' in filename:
            return False
        
        # Alphanumeric, dash, underscore, dot, space only
        pattern = r'^[a-zA-Z0-9._\- ]+$'
        return bool(re.match(pattern, filename))
    
    async def _validate_image(self, content: bytes) -> List[str]:
        """Validate image-specific properties."""
        errors = []
        
        try:
            from PIL import Image
            
            image = Image.open(BytesIO(content))
            
            # Check dimensions
            max_dimensions = 10000  # 10000x10000 max
            if image.width > max_dimensions or image.height > max_dimensions:
                errors.append(f"Image dimensions too large (max: {max_dimensions}x{max_dimensions})")
            
            # Check for decompression bombs
            pixels = image.width * image.height
            max_pixels = 100_000_000  # 100 megapixels
            
            if pixels > max_pixels:
                errors.append("Image has too many pixels (possible decompression bomb)")
        
        except ImportError:
            logger.warning("Pillow not available, skipping image validation")
        except Exception as e:
            errors.append(f"Invalid image: {str(e)}")
        
        return errors
    
    async def scan_for_malware(self, file_content: bytes) -> bool:
        """
        Scan file for malware using ClamAV (optional).
        
        Requires clamd package and ClamAV daemon running.
        
        Returns:
            True if safe, False if malware detected or scan failed
        """
        # Check if ClamAV is enabled in settings
        if not getattr(settings, 'clamav_enabled', False):
            logger.debug("ClamAV scanning disabled in settings")
            return True
        
        try:
            import clamd
            
            # Connect to ClamAV daemon
            socket_path = getattr(settings, 'clamav_socket_path', '/var/run/clamav/clamd.ctl')
            
            try:
                cd = clamd.ClamdUnixSocket(socket_path)
            except:
                # Try network socket if unix socket fails
                cd = clamd.ClamdNetworkSocket()
            
            # Scan
            result = cd.instream(BytesIO(file_content))
            
            # Check result
            scan_result = result['stream'][0]
            if scan_result == 'OK':
                return True
            else:
                logger.warning(f"Malware detected: {scan_result}")
                return False
        
        except ImportError:
            logger.warning("clamd package not available, skipping malware scan")
            return True  # Fail open if package not installed
        
        except Exception as e:
            logger.error(f"Virus scan failed: {e}")
            # Fail closed for security - reject if scan fails
            return False

