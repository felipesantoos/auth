"""
Unit tests for URL Validator utility
Tests SSRF protection logic without external dependencies
"""
import pytest
from core.utils.url_validator import (
    is_private_ip,
    is_safe_url,
    validate_url_or_raise,
    SSRFProtectionError
)


@pytest.mark.unit
class TestPrivateIPDetection:
    """Test private IP detection"""
    
    def test_localhost_ip_detected(self):
        """Test localhost IP is detected as private"""
        assert is_private_ip("127.0.0.1") is True
    
    def test_private_ip_10_network_detected(self):
        """Test 10.x.x.x network is detected as private"""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.255") is True
    
    def test_private_ip_192_network_detected(self):
        """Test 192.168.x.x network is detected as private"""
        assert is_private_ip("192.168.1.1") is True
        assert is_private_ip("192.168.100.50") is True
    
    def test_private_ip_172_network_detected(self):
        """Test 172.16-31.x.x network is detected as private"""
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.255") is True
    
    def test_link_local_detected(self):
        """Test link-local addresses detected as private"""
        assert is_private_ip("169.254.1.1") is True
    
    def test_aws_metadata_endpoint_detected(self):
        """Test AWS metadata endpoint is detected as private"""
        assert is_private_ip("169.254.169.254") is True
    
    def test_ipv6_localhost_detected(self):
        """Test IPv6 localhost is detected as private"""
        assert is_private_ip("::1") is True
    
    def test_public_ip_not_detected(self):
        """Test public IPs are not detected as private"""
        assert is_private_ip("8.8.8.8") is False  # Google DNS
        assert is_private_ip("1.1.1.1") is False  # Cloudflare DNS
    
    def test_hostname_returns_false(self):
        """Test hostnames (not IPs) return False"""
        assert is_private_ip("example.com") is False
        assert is_private_ip("api.github.com") is False


@pytest.mark.unit
class TestSafeURLValidation:
    """Test URL safety validation"""
    
    def test_https_whitelisted_domain_is_safe(self):
        """Test HTTPS URL with whitelisted domain is safe"""
        url = "https://api.github.com/users"
        
        is_safe = is_safe_url(url, allowed_domains=["api.github.com"])
        
        assert is_safe is True
    
    def test_http_rejected_by_default(self):
        """Test HTTP URLs are rejected by default"""
        url = "http://api.github.com/users"
        
        is_safe = is_safe_url(url, allowed_domains=["api.github.com"])
        
        assert is_safe is False
    
    def test_http_allowed_with_flag(self):
        """Test HTTP allowed when flag is set"""
        url = "http://api.github.com/users"
        
        is_safe = is_safe_url(url, allowed_domains=["api.github.com"], allow_http=True)
        
        assert is_safe is True
    
    def test_non_whitelisted_domain_rejected(self):
        """Test non-whitelisted domain is rejected"""
        url = "https://evil.com/api"
        
        is_safe = is_safe_url(url, allowed_domains=["api.github.com"])
        
        assert is_safe is False
    
    def test_localhost_rejected(self):
        """Test localhost URLs are rejected"""
        urls = [
            "https://localhost/admin",
            "https://127.0.0.1/admin",
            "https://0.0.0.0/admin",
        ]
        
        for url in urls:
            is_safe = is_safe_url(url, allowed_domains=["localhost", "127.0.0.1"])
            assert is_safe is False
    
    def test_private_ip_rejected(self):
        """Test private IP addresses are rejected"""
        urls = [
            "https://10.0.0.1/api",
            "https://192.168.1.1/api",
            "https://172.16.0.1/api",
        ]
        
        for url in urls:
            is_safe = is_safe_url(url, allowed_domains=["10.0.0.1"])
            assert is_safe is False
    
    def test_aws_metadata_endpoint_rejected(self):
        """Test AWS metadata endpoint is rejected"""
        url = "https://169.254.169.254/latest/meta-data"
        
        is_safe = is_safe_url(url, allowed_domains=["169.254.169.254"])
        
        assert is_safe is False
    
    def test_empty_url_rejected(self):
        """Test empty URL is rejected"""
        is_safe = is_safe_url("")
        
        assert is_safe is False
    
    def test_url_without_hostname_rejected(self):
        """Test URL without hostname is rejected"""
        url = "https:///path"
        
        is_safe = is_safe_url(url)
        
        assert is_safe is False


@pytest.mark.unit
class TestValidateURLOrRaise:
    """Test URL validation with exception"""
    
    def test_valid_url_returns_url(self):
        """Test valid URL is returned"""
        url = "https://api.github.com/users"
        
        result = validate_url_or_raise(url, allowed_domains=["api.github.com"])
        
        assert result == url
    
    def test_invalid_url_raises_exception(self):
        """Test invalid URL raises SSRFProtectionError"""
        url = "http://localhost/admin"
        
        with pytest.raises(SSRFProtectionError):
            validate_url_or_raise(url)
    
    def test_private_ip_raises_exception(self):
        """Test private IP raises SSRFProtectionError"""
        url = "https://192.168.1.1/api"
        
        with pytest.raises(SSRFProtectionError):
            validate_url_or_raise(url)

