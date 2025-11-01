"""UserSession Mapper - Converts between DB model and domain"""
from core.domain.auth.user_session import UserSession
from infra.database.models.user_session import DBUserSession


class UserSessionMapper:
    """Mapper for UserSession entity"""
    
    @staticmethod
    def to_domain(db_session: DBUserSession) -> UserSession:
        """Converts DB model to domain"""
        return UserSession(
            id=db_session.id,
            user_id=db_session.user_id,
            client_id=db_session.client_id,
            refresh_token_hash=db_session.refresh_token_hash,
            device_name=db_session.device_name,
            device_type=db_session.device_type,
            ip_address=db_session.ip_address,
            user_agent=db_session.user_agent,
            location=db_session.location,
            last_activity=db_session.last_activity,
            created_at=db_session.created_at,
            revoked_at=db_session.revoked_at,
            expires_at=db_session.expires_at,
        )
    
    @staticmethod
    def to_database(session: UserSession, db_session: DBUserSession = None) -> DBUserSession:
        """Converts domain to DB model"""
        if db_session is None:
            db_session = DBUserSession()
        
        db_session.id = session.id
        db_session.user_id = session.user_id
        db_session.client_id = session.client_id
        db_session.refresh_token_hash = session.refresh_token_hash
        db_session.device_name = session.device_name
        db_session.device_type = session.device_type
        db_session.ip_address = session.ip_address
        db_session.user_agent = session.user_agent
        db_session.location = session.location
        db_session.last_activity = session.last_activity
        db_session.created_at = session.created_at
        db_session.revoked_at = session.revoked_at
        db_session.expires_at = session.expires_at
        
        return db_session

