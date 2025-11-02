"""
Unit tests for Client Detection utility
Tests client type detection logic without external dependencies
"""
import pytest
from unittest.mock import Mock
from app.api.utils.client_detection import (
    detect_client_type,
    is_web_client,
    is_mobile_client,
    get_cookie_settings,
    ClientType
)


@pytest.mark.unit
class TestClientTypeDetection:
    """Test client type detection"""
    
    def test_detect_explicit_web_client(self):
        """Test explicit web client detection via header"""
        request = Mock()
        request.headers = {"X-Client-Type": "web"}
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.WEB
    
    def test_detect_explicit_mobile_client(self):
        """Test explicit mobile client detection via header"""
        request = Mock()
        request.headers = {"X-Client-Type": "mobile"}
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.MOBILE
    
    def test_detect_mobile_from_user_agent_okhttp(self):
        """Test mobile detection from OkHttp user agent"""
        request = Mock()
        request.headers = {
            "User-Agent": "okhttp/4.9.0"
        }
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.MOBILE
    
    def test_detect_mobile_from_user_agent_flutter(self):
        """Test mobile detection from Flutter/Dart user agent"""
        request = Mock()
        request.headers = {
            "User-Agent": "Dart/2.18 (dart:io)"
        }
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.MOBILE
    
    def test_detect_web_from_user_agent_chrome(self):
        """Test web detection from Chrome user agent"""
        request = Mock()
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/100.0"
        }
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.WEB
    
    def test_detect_web_from_user_agent_firefox(self):
        """Test web detection from Firefox user agent"""
        request = Mock()
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"
        }
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.WEB
    
    def test_default_to_web_for_unknown_agent(self):
        """Test defaults to WEB for unknown user agent"""
        request = Mock()
        request.headers = {
            "User-Agent": "CustomBot/1.0"
        }
        
        client_type = detect_client_type(request)
        
        assert client_type == ClientType.WEB


@pytest.mark.unit
class TestClientTypeHelpers:
    """Test client type helper functions"""
    
    def test_is_web_client(self):
        """Test is_web_client returns True for web clients"""
        request = Mock()
        request.headers = {"X-Client-Type": "web"}
        
        assert is_web_client(request) is True
    
    def test_is_mobile_client(self):
        """Test is_mobile_client returns True for mobile clients"""
        request = Mock()
        request.headers = {"X-Client-Type": "mobile"}
        
        assert is_mobile_client(request) is True
    
    def test_is_web_client_false_for_mobile(self):
        """Test is_web_client returns False for mobile clients"""
        request = Mock()
        request.headers = {"X-Client-Type": "mobile"}
        
        assert is_web_client(request) is False


@pytest.mark.unit
class TestCookieSettings:
    """Test cookie settings generation"""
    
    def test_get_cookie_settings_web_strict_samesite(self):
        """Test web clients get strict SameSite policy"""
        request = Mock()
        request.headers = {"X-Client-Type": "web"}
        
        with pytest.mock.patch('app.api.utils.client_detection.settings') as mock_settings:
            mock_settings.environment = "production"
            
            settings = get_cookie_settings(request)
            
            assert settings["httponly"] is True
            assert settings["samesite"] == "strict"
    
    def test_get_cookie_settings_mobile_lax_samesite(self):
        """Test mobile clients get lax SameSite policy"""
        request = Mock()
        request.headers = {"X-Client-Type": "mobile"}
        
        with pytest.mock.patch('app.api.utils.client_detection.settings') as mock_settings:
            mock_settings.environment = "production"
            
            settings = get_cookie_settings(request)
            
            assert settings["httponly"] is True
            assert settings["samesite"] == "lax"
    
    def test_get_cookie_settings_secure_in_production(self):
        """Test secure flag is True in production"""
        request = Mock()
        request.headers = {"X-Client-Type": "web"}
        
        with pytest.mock.patch('app.api.utils.client_detection.settings') as mock_settings:
            mock_settings.environment = "production"
            
            settings = get_cookie_settings(request)
            
            assert settings["secure"] is True
    
    def test_get_cookie_settings_not_secure_in_development(self):
        """Test secure flag is False in development"""
        request = Mock()
        request.headers = {"X-Client-Type": "web"}
        
        with pytest.mock.patch('app.api.utils.client_detection.settings') as mock_settings:
            mock_settings.environment = "development"
            
            settings = get_cookie_settings(request)
            
            assert settings["secure"] is False

