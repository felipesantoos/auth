"""
User factory for generating test data
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from faker import Faker

from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole


# Initialize Faker with Portuguese locale
fake = Faker('pt_BR')


class UserFactory:
    """Factory for creating AppUser instances with realistic data"""
    
    @staticmethod
    def build(
        id: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: str = "TestPass123",
        name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        client_id: str = "test-client-id",
        active: bool = True,
        email_verified: bool = False,
        mfa_enabled: bool = False,
        **kwargs
    ) -> AppUser:
        """
        Create a test AppUser with realistic data.
        
        Args:
            id: User ID (auto-generated if not provided)
            username: Username (auto-generated if not provided)
            email: Email (auto-generated if not provided)
            password: Plain password to hash (default: TestPass123)
            name: Full name (auto-generated if not provided)
            role: User role
            client_id: Client ID
            active: Whether user is active
            email_verified: Whether email is verified
            mfa_enabled: Whether MFA is enabled
            **kwargs: Additional fields to override
        
        Returns:
            AppUser instance with realistic test data
        """
        # Generate realistic data if not provided
        if not id:
            id = fake.uuid4()
        if not username:
            username = fake.user_name()[:20]  # Limit length
        if not email:
            email = fake.email()
        if not name:
            name = fake.name()
        
        # Hash the password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        return AppUser(
            id=id,
            username=username,
            email=email,
            _password_hash=password_hash,
            name=name,
            role=role,
            client_id=client_id,
            active=active,
            email_verified=email_verified,
            mfa_enabled=mfa_enabled,
            created_at=kwargs.get('created_at', datetime.utcnow()),
            updated_at=kwargs.get('updated_at', datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k not in ['created_at', 'updated_at']}
        )
    
    @staticmethod
    async def create_persisted(db_session, **kwargs) -> AppUser:
        """
        Create and persist user to database.
        
        Args:
            db_session: Database session
            **kwargs: User attributes
        
        Returns:
            Persisted AppUser with ID from database
        """
        from infra.database.repositories.app_user_repository import AppUserRepository
        
        user = UserFactory.build(**kwargs)
        repository = AppUserRepository(db_session)
        saved = await repository.save(user)
        await db_session.commit()
        return saved
    
    @staticmethod
    async def create_batch_persisted(db_session, count: int, **kwargs) -> list[AppUser]:
        """
        Create and persist multiple users to database.
        
        Args:
            db_session: Database session
            count: Number of users to create
            **kwargs: Common attributes for all users
        
        Returns:
            List of persisted AppUser instances
        """
        users = []
        for _ in range(count):
            user = await UserFactory.create_persisted(db_session, **kwargs)
            users.append(user)
        return users
    
    @staticmethod
    def create_admin(
        client_id: str = "test-client-id",
        **kwargs
    ) -> AppUser:
        """Create a test admin user (in-memory)"""
        return UserFactory.build(
            role=UserRole.ADMIN,
            client_id=client_id,
            email_verified=True,
            **kwargs
        )
    
    @staticmethod
    def create_manager(
        client_id: str = "test-client-id",
        **kwargs
    ) -> AppUser:
        """Create a test manager user (in-memory)"""
        return UserFactory.build(
            role=UserRole.MANAGER,
            client_id=client_id,
            email_verified=True,
            **kwargs
        )
    
    @staticmethod
    def create_with_mfa(
        client_id: str = "test-client-id",
        **kwargs
    ) -> AppUser:
        """Create a test user with MFA enabled (in-memory)"""
        return UserFactory.build(
            client_id=client_id,
            mfa_enabled=True,
            mfa_secret=secrets.token_hex(16),
            email_verified=True,
            **kwargs
        )
    
    @staticmethod
    def create_locked(
        client_id: str = "test-client-id",
        **kwargs
    ) -> AppUser:
        """Create a test user with locked account (in-memory)"""
        return UserFactory.build(
            client_id=client_id,
            failed_login_attempts=5,
            locked_until=datetime.utcnow() + timedelta(minutes=30),
            **kwargs
        )
    
    @staticmethod
    def create_batch(count: int = 5, **kwargs) -> list[AppUser]:
        """Create multiple test users (in-memory)"""
        return [UserFactory.build(**kwargs) for _ in range(count)]


class UserFactoryTraits:
    """Predefined user configurations (Trait pattern)"""
    
    @staticmethod
    def active() -> AppUser:
        """Create active user"""
        return UserFactory.build(active=True)
    
    @staticmethod
    def inactive() -> AppUser:
        """Create inactive user"""
        return UserFactory.build(active=False)
    
    @staticmethod
    def with_verified_email() -> AppUser:
        """Create user with verified email"""
        return UserFactory.build(email_verified=True)
    
    @staticmethod
    def with_unverified_email() -> AppUser:
        """Create user with unverified email"""
        return UserFactory.build(email_verified=False)
    
    @staticmethod
    def with_mfa() -> AppUser:
        """Create user with MFA enabled"""
        return UserFactory.create_with_mfa()
    
    @staticmethod
    def locked() -> AppUser:
        """Create locked user"""
        return UserFactory.create_locked()
    
    @staticmethod
    def minimal() -> AppUser:
        """Create minimal valid user"""
        return UserFactory.build(
            username="test",
            email="test@test.com",
            name="Test User"
        )

