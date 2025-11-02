"""
Suspicious Activity Detector Interface
Primary port for detecting suspicious authentication patterns
"""
from abc import ABC, abstractmethod
from typing import Optional


class ISuspiciousActivityDetector(ABC):
    """
    Interface for detecting suspicious activity patterns.
    
    Provides methods to detect:
    - Location changes (impossible travel)
    - New devices
    - New IP addresses
    - Overall suspicious activity
    """
    
    @abstractmethod
    async def check_location_change(
        self,
        user_id: str,
        client_id: str,
        current_location: str,
        current_ip: str
    ) -> bool:
        """
        Detect impossible travel (login from distant locations in short time).
        
        Args:
            user_id: User ID
            client_id: Client ID
            current_location: Current login location
            current_ip: Current IP address
            
        Returns:
            True if suspicious location change detected
        """
        pass
    
    @abstractmethod
    async def check_new_device(
        self,
        user_id: str,
        client_id: str,
        user_agent: str,
        ip_address: str
    ) -> bool:
        """
        Check if login is from a new device.
        
        Args:
            user_id: User ID
            client_id: Client ID
            user_agent: User agent string
            ip_address: IP address
            
        Returns:
            True if this is a new device/IP combination
        """
        pass
    
    @abstractmethod
    async def detect_impossible_travel(
        self,
        user_id: str,
        client_id: str,
        current_location: str
    ) -> bool:
        """
        Detect impossible travel based on previous login locations.
        
        Args:
            user_id: User ID
            client_id: Client ID
            current_location: Current location
            
        Returns:
            True if impossible travel detected
        """
        pass
    
    @abstractmethod
    async def detect_suspicious_activity(
        self,
        user_id: str,
        client_id: str,
        ip_address: str,
        user_agent: str,
        location: Optional[str] = None
    ) -> bool:
        """
        Comprehensive suspicious activity detection.
        
        Combines multiple detection methods.
        
        Args:
            user_id: User ID
            client_id: Client ID
            ip_address: IP address
            user_agent: User agent
            location: Optional location
            
        Returns:
            True if suspicious activity detected
        """
        pass

