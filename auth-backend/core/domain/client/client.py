"""
Client Domain Model
Represents a tenant/client in the multi-tenant system
"""
import secrets
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Client:
    """
    Domain model for client (tenant).
    
    Each client represents a separate tenant with isolated users.
    This is pure business logic with no framework dependencies.
    """
    id: Optional[str]
    name: str
    subdomain: str
    api_key: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Business validation rules"""
        if not self.name or len(self.name) < 3:
            raise ValueError("Client name must have at least 3 characters")
        
        if not self.subdomain or len(self.subdomain) < 2:
            raise ValueError("Subdomain must have at least 2 characters")
        
        # Subdomain should be lowercase alphanumeric with hyphens
        if not all(c.isalnum() or c == '-' for c in self.subdomain.lower()):
            raise ValueError("Subdomain can only contain alphanumeric characters and hyphens")
    
    def activate(self) -> None:
        """Business operation to activate client"""
        self.active = True
    
    def deactivate(self) -> None:
        """Business operation to deactivate client"""
        self.active = False
    
    def generate_api_key(self) -> str:
        """Generate a new API key for the client"""
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key

