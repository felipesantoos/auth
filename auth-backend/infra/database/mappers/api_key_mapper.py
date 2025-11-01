"""ApiKey Mapper - Converts between DB model and domain"""
from core.domain.auth.api_key import ApiKey
from core.domain.auth.api_key_scope import ApiKeyScope
from infra.database.models.api_key import DBApiKey


class ApiKeyMapper:
    """Mapper for ApiKey entity"""
    
    @staticmethod
    def to_domain(db_key: DBApiKey) -> ApiKey:
        """Converts DB model to domain"""
        scopes = [ApiKeyScope(scope) for scope in db_key.scopes]
        
        return ApiKey(
            id=db_key.id,
            user_id=db_key.user_id,
            client_id=db_key.client_id,
            name=db_key.name,
            key_hash=db_key.key_hash,
            scopes=scopes,
            last_used_at=db_key.last_used_at,
            expires_at=db_key.expires_at,
            created_at=db_key.created_at,
            revoked_at=db_key.revoked_at,
        )
    
    @staticmethod
    def to_database(key: ApiKey, db_key: DBApiKey = None) -> DBApiKey:
        """Converts domain to DB model"""
        if db_key is None:
            db_key = DBApiKey()
        
        db_key.id = key.id
        db_key.user_id = key.user_id
        db_key.client_id = key.client_id
        db_key.name = key.name
        db_key.key_hash = key.key_hash
        db_key.scopes = [scope.value for scope in key.scopes]
        db_key.last_used_at = key.last_used_at
        db_key.expires_at = key.expires_at
        db_key.created_at = key.created_at
        db_key.revoked_at = key.revoked_at
        
        return db_key

