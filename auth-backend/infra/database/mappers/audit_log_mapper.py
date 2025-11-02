"""AuditLog Mapper - Converts between DB model and domain"""
from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from infra.database.models.audit_log import DBAuditLog


class AuditLogMapper:
    """Mapper for AuditLog entity"""
    
    @staticmethod
    def to_domain(db_log: DBAuditLog) -> AuditLog:
        """Converts DB model to domain"""
        return AuditLog(
            id=db_log.id,
            user_id=db_log.user_id,
            client_id=db_log.client_id,
            event_type=AuditEventType(db_log.event_type),
            resource_type=db_log.resource_type,
            resource_id=db_log.resource_id,
            ip_address=db_log.ip_address,
            user_agent=db_log.user_agent,
            metadata=db_log.event_metadata,
            status=db_log.status,
            created_at=db_log.created_at,
        )
    
    @staticmethod
    def to_database(log: AuditLog, db_log: DBAuditLog = None) -> DBAuditLog:
        """Converts domain to DB model"""
        if db_log is None:
            db_log = DBAuditLog()
        
        db_log.id = log.id
        db_log.user_id = log.user_id
        db_log.client_id = log.client_id
        db_log.event_type = log.event_type.value
        db_log.resource_type = log.resource_type
        db_log.resource_id = log.resource_id
        db_log.ip_address = log.ip_address
        db_log.user_agent = log.user_agent
        db_log.event_metadata = log.metadata
        db_log.status = log.status
        db_log.created_at = log.created_at
        
        return db_log

