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
            name=db_user.full_name,
            role=UserRole(db_user.role),
            client_id=db_user.client_id,  # Multi-tenant
            active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            _password_hash=db_user.hashed_password,  # Use protected field for encapsulation
            # Email Verification
            email_verified=db_user.email_verified,
            email_verification_token=db_user.email_verification_token,
            email_verification_sent_at=db_user.email_verification_sent_at,
            # MFA/2FA
            mfa_enabled=db_user.mfa_enabled,
            mfa_secret=db_user.mfa_secret,
            # Account Security
            failed_login_attempts=db_user.failed_login_attempts,
            locked_until=db_user.locked_until,
            # Passwordless Auth
            magic_link_token=db_user.magic_link_token,
            magic_link_sent_at=db_user.magic_link_sent_at,
        )
    
    @staticmethod
    def to_database(user: AppUser, db_user: DBAppUser = None) -> DBAppUser:
        """Converts domain to DB model"""
        if db_user is None:
            db_user = DBAppUser()
        
        db_user.id = user.id
        db_user.username = user.username
        db_user.email = user.email
        db_user.hashed_password = user.password_hash  # Access via property (encapsulation)
        db_user.full_name = user.name
        db_user.role = user.role.value
        db_user.is_active = user.active
        db_user.client_id = user.client_id  # Multi-tenant
        db_user.created_at = user.created_at
        db_user.updated_at = user.updated_at
        
        # Email Verification
        db_user.email_verified = user.email_verified
        db_user.email_verification_token = user.email_verification_token
        db_user.email_verification_sent_at = user.email_verification_sent_at
        
        # MFA/2FA
        db_user.mfa_enabled = user.mfa_enabled
        db_user.mfa_secret = user.mfa_secret
        
        # Account Security
        db_user.failed_login_attempts = user.failed_login_attempts
        db_user.locked_until = user.locked_until
        
        # Passwordless Auth
        db_user.magic_link_token = user.magic_link_token
        db_user.magic_link_sent_at = user.magic_link_sent_at
        
        return db_user

