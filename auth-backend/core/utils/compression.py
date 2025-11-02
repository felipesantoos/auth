"""
Compression Utilities
Utilities for compressing data before storage (database, cache, etc.)
"""
import gzip
import base64
import json
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class CompressedJSONField:
    """
    Utility for compressing large JSON data before storing in database.
    
    Use this for:
    - User preferences (can be 10MB+)
    - File metadata
    - Audit logs with large payloads
    - Any JSONB field > 1KB
    
    Benefits:
    - 70-90% size reduction
    - Faster database queries (less data to read)
    - Lower storage costs
    - Reduced backup sizes
    
    Example:
        >>> # Compress before saving to database
        >>> compressed = CompressedJSONField.compress(large_settings)
        >>> user.settings_compressed = compressed
        >>> 
        >>> # Decompress when reading
        >>> settings = CompressedJSONField.decompress(user.settings_compressed)
    """
    
    @staticmethod
    def compress(data: Dict[str, Any]) -> str:
        """
        Compress JSON data using gzip.
        
        Args:
            data: Dictionary to compress
            
        Returns:
            Base64-encoded compressed string (safe for database storage)
            
        Example:
            >>> data = {"key": "value", "nested": {"foo": "bar"}}
            >>> compressed = CompressedJSONField.compress(data)
            >>> len(compressed) < len(json.dumps(data))  # True
        """
        try:
            # Serialize to JSON (compact, no whitespace)
            json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            
            # Compress with gzip (level 9 = max compression)
            compressed = gzip.compress(json_str.encode('utf-8'), compresslevel=9)
            
            # Encode to base64 for safe database storage
            encoded = base64.b64encode(compressed).decode('utf-8')
            
            compression_ratio = (1 - len(encoded) / len(json_str)) * 100
            logger.debug(
                f"JSON compressed: {len(json_str)} -> {len(encoded)} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )
            
            return encoded
            
        except Exception as e:
            logger.error(f"Failed to compress JSON: {e}")
            raise
    
    @staticmethod
    def decompress(compressed_str: str) -> Dict[str, Any]:
        """
        Decompress JSON data.
        
        Args:
            compressed_str: Base64-encoded compressed string
            
        Returns:
            Original dictionary
            
        Raises:
            ValueError: If decompression fails
            
        Example:
            >>> compressed = CompressedJSONField.compress({"key": "value"})
            >>> data = CompressedJSONField.decompress(compressed)
            >>> data["key"]
            'value'
        """
        try:
            # Decode from base64
            compressed = base64.b64decode(compressed_str.encode('utf-8'))
            
            # Decompress
            json_str = gzip.decompress(compressed).decode('utf-8')
            
            # Parse JSON
            data = json.loads(json_str)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to decompress JSON: {e}")
            raise ValueError(f"Invalid compressed data: {e}")
    
    @staticmethod
    def should_compress(data: Dict[str, Any], threshold_bytes: int = 1024) -> bool:
        """
        Check if data should be compressed based on size threshold.
        
        Args:
            data: Dictionary to check
            threshold_bytes: Minimum size in bytes to compress (default: 1KB)
            
        Returns:
            True if data should be compressed
            
        Example:
            >>> small_data = {"key": "value"}
            >>> CompressedJSONField.should_compress(small_data)
            False
            >>> 
            >>> large_data = {"key": "x" * 10000}
            >>> CompressedJSONField.should_compress(large_data)
            True
        """
        json_str = json.dumps(data, separators=(',', ':'))
        size_bytes = len(json_str.encode('utf-8'))
        return size_bytes > threshold_bytes


# Example SQLAlchemy property usage
"""
from sqlalchemy import Column, String, Text
from core.utils.compression import CompressedJSONField

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    
    # Store compressed JSON
    _settings_compressed = Column("settings_compressed", Text, nullable=False)
    
    @property
    def settings(self) -> dict:
        '''Get decompressed settings.'''
        return CompressedJSONField.decompress(self._settings_compressed)
    
    @settings.setter
    def settings(self, value: dict):
        '''Set and compress settings.'''
        self._settings_compressed = CompressedJSONField.compress(value)


# Usage
user_prefs = UserPreferences(id=str(uuid.uuid4()), user_id=user.id)

# Set large settings (automatically compressed)
user_prefs.settings = {
    "theme": "dark",
    "notifications": {...},  # Large nested object
    "filters": [...],  # Large arrays
    # ... 10MB of settings
}

await db.save(user_prefs)

# Read settings (automatically decompressed)
settings = user_prefs.settings
"""


class StreamingCompressor:
    """
    Streaming compression for large files or data streams.
    
    Use this for:
    - Large file uploads (> 100MB)
    - Streaming responses
    - Log file compression
    
    Example:
        >>> with StreamingCompressor("/tmp/output.gz") as compressor:
        ...     for chunk in large_data_chunks:
        ...         compressor.write(chunk)
    """
    
    def __init__(self, output_path: str, compresslevel: int = 6):
        """
        Initialize streaming compressor.
        
        Args:
            output_path: Path to output file
            compresslevel: Compression level (1-9)
        """
        self.output_path = output_path
        self.compresslevel = compresslevel
        self.file = None
    
    def __enter__(self):
        """Open compressed file for writing."""
        self.file = gzip.open(
            self.output_path,
            'wb',
            compresslevel=self.compresslevel
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close compressed file."""
        if self.file:
            self.file.close()
    
    def write(self, data: bytes):
        """
        Write data chunk to compressed file.
        
        Args:
            data: Bytes to compress and write
        """
        if not self.file:
            raise ValueError("Compressor not initialized. Use 'with' statement.")
        self.file.write(data)
    
    async def write_async(self, data: bytes):
        """
        Async version of write (for compatibility).
        
        Note: gzip.open doesn't support true async I/O,
        but this method ensures API compatibility.
        """
        self.write(data)


# Example streaming compression usage
"""
from core.utils.compression import StreamingCompressor

# Compress large file
async def compress_large_file(input_path: str, output_path: str):
    '''Compress large file in chunks (memory efficient).'''
    with StreamingCompressor(output_path) as compressor:
        with open(input_path, 'rb') as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                compressor.write(chunk)
    
    logger.info(f"File compressed: {input_path} -> {output_path}")


# Compress logs
async def compress_audit_logs(logs: list):
    '''Compress audit logs before archiving.'''
    with StreamingCompressor("/var/logs/audit.gz") as compressor:
        for log_entry in logs:
            json_line = json.dumps(log_entry) + "\\n"
            compressor.write(json_line.encode('utf-8'))
"""

