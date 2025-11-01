"""
Backup Code factory for generating test data
"""
from datetime import datetime
from typing import Optional, List
import bcrypt
from faker import Faker

from core.domain.auth.backup_code import BackupCode


# Initialize Faker with Portuguese locale
fake = Faker('pt_BR')


class BackupCodeFactory:
    """Factory for creating BackupCode instances with realistic data"""
    
    @staticmethod
    def build(
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
    async def create_persisted(db_session, **kwargs) -> BackupCode:
        """Create and persist backup code to database"""
        from infra.database.repositories.backup_code_repository import BackupCodeRepository
        
        code = BackupCodeFactory.build(**kwargs)
        repository = BackupCodeRepository(db_session)
        saved = await repository.save(code)
        await db_session.commit()
        return saved
    
    @staticmethod
    def create_used(
        user_id: str,
        client_id: str = "test-client-id",
        **kwargs
    ) -> BackupCode:
        """Create a used backup code"""
        return BackupCodeFactory.build(
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
        """Create a batch of backup codes for a user (in-memory)"""
        return [
            BackupCodeFactory.build(
                user_id=user_id,
                client_id=client_id,
                code=f"{fake.random_number(digits=8, fix_len=True)}"
            )
            for _ in range(count)
        ]


class BackupCodeFactoryTraits:
    """Predefined backup code configurations (Trait pattern)"""
    
    @staticmethod
    def unused(user_id: str) -> BackupCode:
        """Create unused backup code"""
        return BackupCodeFactory.build(
            user_id=user_id,
            used=False
        )
    
    @staticmethod
    def used(user_id: str) -> BackupCode:
        """Create used backup code"""
        return BackupCodeFactory.create_used(user_id=user_id)
    
    @staticmethod
    def minimal(user_id: str) -> BackupCode:
        """Create minimal valid backup code"""
        return BackupCodeFactory.build(
            user_id=user_id,
            code="12345678"
        )

