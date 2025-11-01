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
    def create(
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
    def create_admin(
        client_id: str = "test-client-id",
        **kwargs
    ) -> AppUser:
        """Create a test admin user"""
        return UserFactory.create(
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
        """Create a test manager user"""
        return UserFactory.create(
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
        """Create a test user with MFA enabled"""
        return UserFactory.create(
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
        """Create a test user with locked account"""
        return UserFactory.create(
            client_id=client_id,
            failed_login_attempts=5,
            locked_until=datetime.utcnow() + timedelta(minutes=30),
            **kwargs
        )
    
    @staticmethod
    def create_batch(count: int = 5, **kwargs) -> list[AppUser]:
        """Create multiple test users"""
        return [UserFactory.create(**kwargs) for _ in range(count)]

