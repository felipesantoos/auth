"""
Unit tests for Compression utilities
Tests compression logic without external dependencies
"""
import pytest
import json
from core.utils.compression import CompressedJSONField, StreamingCompressor


@pytest.mark.unit
class TestCompressedJSONField:
    """Test JSON compression utilities"""
    
    def test_compress_and_decompress_preserves_data(self):
        """Test compression and decompression preserves data"""
        original = {
            "name": "John Doe",
            "email": "john@example.com",
            "settings": {
                "theme": "dark",
                "language": "en"
            }
        }
        
        compressed = CompressedJSONField.compress(original)
        decompressed = CompressedJSONField.decompress(compressed)
        
        assert decompressed == original
    
    def test_compress_reduces_size(self):
        """Test compression actually reduces size for large data"""
        large_data = {
            "data": "x" * 10000,  # Large repeated string
            "nested": {f"key{i}": f"value{i}" for i in range(100)}
        }
        
        compressed = CompressedJSONField.compress(large_data)
        original_size = len(json.dumps(large_data))
        compressed_size = len(compressed)
        
        # Compressed should be smaller (especially for repetitive data)
        assert compressed_size < original_size
    
    def test_decompress_invalid_data_raises_error(self):
        """Test decompressing invalid data raises error"""
        invalid_compressed = "invalid_base64_data"
        
        with pytest.raises(ValueError):
            CompressedJSONField.decompress(invalid_compressed)
    
    def test_should_compress_large_data(self):
        """Test should_compress returns True for large data"""
        large_data = {"data": "x" * 2000}  # > 1KB
        
        should_compress = CompressedJSONField.should_compress(large_data, threshold_bytes=1024)
        
        assert should_compress is True
    
    def test_should_not_compress_small_data(self):
        """Test should_compress returns False for small data"""
        small_data = {"key": "value"}  # < 1KB
        
        should_compress = CompressedJSONField.should_compress(small_data, threshold_bytes=1024)
        
        assert should_compress is False
    
    def test_compress_empty_dict(self):
        """Test compressing empty dictionary"""
        empty = {}
        
        compressed = CompressedJSONField.compress(empty)
        decompressed = CompressedJSONField.decompress(compressed)
        
        assert decompressed == empty
    
    def test_compress_nested_structures(self):
        """Test compressing deeply nested structures"""
        nested = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [1, 2, 3, 4, 5]
                    }
                }
            }
        }
        
        compressed = CompressedJSONField.compress(nested)
        decompressed = CompressedJSONField.decompress(compressed)
        
        assert decompressed == nested


@pytest.mark.unit
class TestStreamingCompressor:
    """Test streaming compression utilities"""
    
    def test_streaming_compressor_context_manager(self, tmp_path):
        """Test streaming compressor as context manager"""
        output_file = tmp_path / "test.gz"
        
        with StreamingCompressor(str(output_file)) as compressor:
            compressor.write(b"Hello World")
            compressor.write(b" More data")
        
        assert output_file.exists()
    
    def test_write_without_context_raises_error(self):
        """Test writing without context manager raises error"""
        compressor = StreamingCompressor("/tmp/test.gz")
        
        with pytest.raises(ValueError, match="not initialized"):
            compressor.write(b"data")
    
    @pytest.mark.asyncio
    async def test_async_write(self, tmp_path):
        """Test async write method"""
        output_file = tmp_path / "test_async.gz"
        
        with StreamingCompressor(str(output_file)) as compressor:
            await compressor.write_async(b"Async data")
        
        assert output_file.exists()

