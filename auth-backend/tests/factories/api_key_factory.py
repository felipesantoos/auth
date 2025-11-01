"""
API Key factory for generating test data
"""
from datetime import datetime, timedelta
from typing import Optional, List
import bcrypt
from faker import Faker

from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope


# Initialize Faker with Portuguese locale
fake = Faker('pt_BR')


class ApiKeyFactory:
    """Factory for creating ApiKey instances with realistic data"""
    
    @staticmethod
    def build(
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        client_id: str = "test-client-id",
        name: Optional[str] = None,
        key: str = "test-key",
        scopes: Optional[List[ApiKeyScope]] = None,
        expires_at: Optional[datetime] = None,
        revoked_at: Optional[datetime] = None,
        **kwargs
    ) -> ApiKey:
        """
        Create a test ApiKey with realistic data.
        
        Args:
            id: API key ID (auto-generated if not provided)
            user_id: User ID (auto-generated if not provided)
            client_id: Client ID
            name: Key name (auto-generated if not provided)
            key: Plain key to hash (default: test-key)
            scopes: List of scopes (default: [READ])
            expires_at: Expiration datetime (default: 30 days from now)
            revoked_at: Revocation datetime (None if not revoked)
            **kwargs: Additional fields to override
        
        Returns:
            ApiKey instance with realistic test data
        """
        if not id:
            id = fake.uuid4()
        if not user_id:
            user_id = fake.uuid4()
        if not name:
            name = f"{fake.word()} API Key"[:50]
        if scopes is None:
            scopes = [ApiKeyScope.READ]
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Hash the key
        key_hash = bcrypt.hashpw(
            key.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        return ApiKey(
            id=id,
            user_id=user_id,
            client_id=client_id,
            name=name,
            key_hash=key_hash,
            scopes=scopes,
            expires_at=expires_at,
            revoked_at=revoked_at,
            last_used_at=kwargs.get('last_used_at'),
            created_at=kwargs.get('created_at', datetime.utcnow())
        )
    
    @staticmethod
    async def create_persisted(db_session, **kwargs) -> ApiKey:
        """Create and persist API key to database"""
        from infra.database.repositories.api_key_repository import ApiKeyRepository
        
        api_key = ApiKeyFactory.build(**kwargs)
        repository = ApiKeyRepository(db_session)
        saved = await repository.save(api_key)
        await db_session.commit()
        return saved
    
    @staticmethod
    def create_admin_key(
        user_id: str,
        client_id: str = "test-client-id",
        **kwargs
    ) -> ApiKey:
        """Create an API key with admin scope"""
        return ApiKeyFactory.build(
            user_id=user_id,
            client_id=client_id,
            scopes=[ApiKeyScope.ADMIN],
            **kwargs
        )
    
    @staticmethod
    def create_expired_key(
        user_id: str,
        client_id: str = "test-client-id",
        **kwargs
    ) -> ApiKey:
        """Create an expired API key"""
        return ApiKeyFactory.build(
            user_id=user_id,
            client_id=client_id,
            expires_at=datetime.utcnow() - timedelta(days=1),
            **kwargs
        )
    
    @staticmethod
    def create_revoked_key(
        user_id: str,
        client_id: str = "test-client-id",
        **kwargs
    ) -> ApiKey:
        """Create a revoked API key"""
        return ApiKeyFactory.build(
            user_id=user_id,
            client_id=client_id,
            revoked_at=datetime.utcnow(),
            **kwargs
        )


class ApiKeyFactoryTraits:
    """Predefined API key configurations (Trait pattern)"""
    
    @staticmethod
    def active(user_id: str) -> ApiKey:
        """Create active API key"""
        return ApiKeyFactory.build(
            user_id=user_id,
            revoked_at=None,
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
    
    @staticmethod
    def expired(user_id: str) -> ApiKey:
        """Create expired API key"""
        return ApiKeyFactory.create_expired_key(user_id=user_id)
    
    @staticmethod
    def revoked(user_id: str) -> ApiKey:
        """Create revoked API key"""
        return ApiKeyFactory.create_revoked_key(user_id=user_id)
    
    @staticmethod
    def admin_scope(user_id: str) -> ApiKey:
        """Create API key with admin scope"""
        return ApiKeyFactory.create_admin_key(user_id=user_id)
    
    @staticmethod
    def minimal(user_id: str) -> ApiKey:
        """Create minimal valid API key"""
        return ApiKeyFactory.build(
            user_id=user_id,
            name="Test Key",
            scopes=[ApiKeyScope.READ]
        )

