"""AppUser Mapper - Converts between DB model and domain"""
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from infra.database.models.app_user import DBAppUser


class AppUserMapper:
    """Mapper for AppUser entity"""
    
    @staticmethod
    def to_domain(db_user: DBAppUser) -> AppUser:
        """Converts DB model to domain (anti-corruption layer)"""
        return AppUser(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            password_hash=db_user.hashed_password,
            name=db_user.full_name,
            role=UserRole(db_user.role),
            client_id=db_user.client_id,  # Multi-tenant
            active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )
    
    @staticmethod
    def to_database(user: AppUser, db_user: DBAppUser = None) -> DBAppUser:
        """Converts domain to DB model"""
        if db_user is None:
            db_user = DBAppUser()
        
        db_user.id = user.id
        db_user.username = user.username
        db_user.email = user.email
        db_user.hashed_password = user.password_hash
        db_user.full_name = user.name
        db_user.role = user.role.value
        db_user.is_active = user.active
        db_user.client_id = user.client_id  # Multi-tenant
        db_user.created_at = user.created_at
        db_user.updated_at = user.updated_at
        
        return db_user

