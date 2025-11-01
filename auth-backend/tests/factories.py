"""
Test Data Factories
Generate realistic test data using Faker
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
import bcrypt
from faker import Faker

from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.domain.auth.permission import Permission, PermissionAction
from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope
from core.domain.auth.backup_code import BackupCode
from core.domain.client.client import Client


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


class PermissionFactory:
    """Factory for creating Permission instances with realistic data"""
    
    @staticmethod
    def create(
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        client_id: str = "test-client-id",
        resource_type: str = "project",
        resource_id: Optional[str] = None,
        action: PermissionAction = PermissionAction.READ,
        granted_by: Optional[str] = None,
        **kwargs
    ) -> Permission:
        """
        Create a test Permission with realistic data.
        
        Args:
            id: Permission ID (auto-generated if not provided)
            user_id: User ID (auto-generated if not provided)
            client_id: Client ID
            resource_type: Type of resource (e.g., "project", "ticket")
            resource_id: Specific resource ID (None for all resources)
            action: Permission action
            granted_by: ID of user who granted permission
            **kwargs: Additional fields to override
        
        Returns:
            Permission instance with realistic test data
        """
        if not id:
            id = fake.uuid4()
        if not user_id:
            user_id = fake.uuid4()
        if not resource_id:
            resource_id = fake.uuid4()
        if not granted_by:
            granted_by = fake.uuid4()
        
        return Permission(
            id=id,
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            granted_by=granted_by,
            created_at=kwargs.get('created_at', datetime.utcnow())
        )
    
    @staticmethod
    def create_manage_permission(
        user_id: str,
        client_id: str = "test-client-id",
        resource_type: str = "project",
        resource_id: Optional[str] = None,
        **kwargs
    ) -> Permission:
        """Create a MANAGE permission (grants all actions)"""
        return PermissionFactory.create(
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=PermissionAction.MANAGE,
            **kwargs
        )
    
    @staticmethod
    def create_wildcard_permission(
        user_id: str,
        client_id: str = "test-client-id",
        resource_type: str = "project",
        action: PermissionAction = PermissionAction.READ,
        **kwargs
    ) -> Permission:
        """Create a wildcard permission (applies to all resources of a type)"""
        return PermissionFactory.create(
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=None,  # None means all resources
            action=action,
            **kwargs
        )


class ApiKeyFactory:
    """Factory for creating ApiKey instances with realistic data"""
    
    @staticmethod
    def create(
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
    def create_admin_key(
        user_id: str,
        client_id: str = "test-client-id",
        **kwargs
    ) -> ApiKey:
        """Create an API key with admin scope"""
        return ApiKeyFactory.create(
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
        return ApiKeyFactory.create(
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
        return ApiKeyFactory.create(
            user_id=user_id,
            client_id=client_id,
            revoked_at=datetime.utcnow(),
            **kwargs
        )


class BackupCodeFactory:
    """Factory for creating BackupCode instances with realistic data"""
    
    @staticmethod
    def create(
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        client_id: str = "test-client-id",
        code: str = "12345678",
        used: bool = False,
        used_at: Optional[datetime] = None,
        **kwargs
    ) -> BackupCode:
        """
        Create a test BackupCode with realistic data.
        
        Args:
            id: Backup code ID (auto-generated if not provided)
            user_id: User ID (auto-generated if not provided)
            client_id: Client ID
            code: Plain code to hash (default: 12345678)
            used: Whether code has been used
            used_at: When code was used
            **kwargs: Additional fields to override
        
        Returns:
            BackupCode instance with realistic test data
        """
        if not id:
            id = fake.uuid4()
        if not user_id:
            user_id = fake.uuid4()
        
        # Hash the code
        code_hash = bcrypt.hashpw(
            code.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        
        return BackupCode(
            id=id,
            user_id=user_id,
            client_id=client_id,
            code_hash=code_hash,
            used=used,
            used_at=used_at,
            created_at=kwargs.get('created_at', datetime.utcnow())
        )
    
    @staticmethod
    def create_used(
        user_id: str,
        client_id: str = "test-client-id",
        **kwargs
    ) -> BackupCode:
        """Create a used backup code"""
        return BackupCodeFactory.create(
            user_id=user_id,
            client_id=client_id,
            used=True,
            used_at=datetime.utcnow(),
            **kwargs
        )
    
    @staticmethod
    def create_batch(
        user_id: str,
        client_id: str = "test-client-id",
        count: int = 10
    ) -> List[BackupCode]:
        """Create a batch of backup codes for a user"""
        return [
            BackupCodeFactory.create(
                user_id=user_id,
                client_id=client_id,
                code=f"{fake.random_number(digits=8, fix_len=True)}"
            )
            for _ in range(count)
        ]

