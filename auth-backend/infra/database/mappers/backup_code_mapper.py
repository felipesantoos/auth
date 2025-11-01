"""BackupCode Mapper - Converts between DB model and domain"""
from core.domain.auth.backup_code import BackupCode
from infra.database.models.backup_code import DBBackupCode


class BackupCodeMapper:
    """Mapper for BackupCode entity"""
    
    @staticmethod
    def to_domain(db_code: DBBackupCode) -> BackupCode:
        """Converts DB model to domain"""
        return BackupCode(
            id=db_code.id,
            user_id=db_code.user_id,
            client_id=db_code.client_id,
            code_hash=db_code.code_hash,
            used=db_code.used,
            used_at=db_code.used_at,
            created_at=db_code.created_at,
        )
    
    @staticmethod
    def to_database(code: BackupCode, db_code: DBBackupCode = None) -> DBBackupCode:
        """Converts domain to DB model"""
        if db_code is None:
            db_code = DBBackupCode()
        
        db_code.id = code.id
        db_code.user_id = code.user_id
        db_code.client_id = code.client_id
        db_code.code_hash = code.code_hash
        db_code.used = code.used
        db_code.used_at = code.used_at
        db_code.created_at = code.created_at
        
        return db_code

