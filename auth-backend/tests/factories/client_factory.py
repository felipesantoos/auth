"""
Client factory for generating test data
"""
import secrets
from datetime import datetime
from typing import Optional
from faker import Faker

from core.domain.client.client import Client


# Initialize Faker with Portuguese locale
fake = Faker('pt_BR')


class ClientFactory:
    """Factory for creating Client instances with realistic data"""
    
    @staticmethod
    def create(
        id: Optional[str] = None,
        name: Optional[str] = None,
        subdomain: Optional[str] = None,
        active: bool = True,
        **kwargs
    ) -> Client:
        """
        Create a test Client with realistic data.
        
        Args:
            id: Client ID (auto-generated if not provided)
            name: Client name (auto-generated if not provided)
            subdomain: Subdomain (auto-generated if not provided)
            active: Whether client is active
            **kwargs: Additional fields to override
        
        Returns:
            Client instance with realistic test data
        """
        if not id:
            id = fake.uuid4()
        if not name:
            name = fake.company()[:50]  # Limit length
        if not subdomain:
            # Generate a valid subdomain (lowercase, alphanumeric with hyphens)
            subdomain = fake.slug()[:20]
        
        # Generate API key
        api_key = f"ck_{secrets.token_hex(32)}"
        
        return Client(
            id=id,
            name=name,
            subdomain=subdomain,
            active=active,
            _api_key=api_key,
            created_at=kwargs.get('created_at', datetime.utcnow()),
            updated_at=kwargs.get('updated_at', datetime.utcnow())
        )
