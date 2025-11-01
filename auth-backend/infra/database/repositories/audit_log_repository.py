"""
Audit Log Repository Implementation
Handles persistence of audit logs
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from infra.database.models.audit_log import DBAuditLog
from infra.database.mappers.audit_log_mapper import AuditLogMapper

logger = logging.getLogger(__name__)


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = AuditLogMapper
    
    async def save(self, audit_log: AuditLog) -> AuditLog:
        """
        Save audit log to database.
        
        Args:
            audit_log: AuditLog domain object
            
        Returns:
            Saved AuditLog with ID
        """
        try:
            db_log = self.mapper.to_database(audit_log)
            self.session.add(db_log)
            await self.session.flush()
            await self.session.refresh(db_log)
            
            return self.mapper.to_domain(db_log)
            
        except Exception as e:
            logger.error(f"Error saving audit log: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def find_by_user(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Find audit logs for a specific user.
        
        Args:
            user_id: User ID
            client_id: Optional client ID filter
            event_types: Optional filter by event types
            days: Number of days to look back (default 30)
            limit: Maximum results (default 100)
            
        Returns:
            List of audit logs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(DBAuditLog).where(
                and_(
                    DBAuditLog.user_id == user_id,
                    DBAuditLog.created_at >= cutoff_date
                )
            )
            
            if client_id:
                query = query.where(DBAuditLog.client_id == client_id)
            
            if event_types:
                event_type_values = [et.value for et in event_types]
                query = query.where(DBAuditLog.event_type.in_(event_type_values))
            
            query = query.order_by(desc(DBAuditLog.created_at)).limit(limit)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
            
        except Exception as e:
            logger.error(f"Error finding audit logs by user: {e}", exc_info=True)
            return []
    
    async def find_by_client(
        self,
        client_id: str,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 1000
    ) -> List[AuditLog]:
        """
        Find audit logs for a client (tenant).
        
        Args:
            client_id: Client ID
            event_types: Optional filter by event types
            days: Number of days to look back (default 30)
            limit: Maximum results (default 1000)
            
        Returns:
            List of audit logs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(DBAuditLog).where(
                and_(
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= cutoff_date
                )
            )
            
            if event_types:
                event_type_values = [et.value for et in event_types]
                query = query.where(DBAuditLog.event_type.in_(event_type_values))
            
            query = query.order_by(desc(DBAuditLog.created_at)).limit(limit)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
            
        except Exception as e:
            logger.error(f"Error finding audit logs by client: {e}", exc_info=True)
            return []
    
    async def find_security_events(
        self,
        client_id: str,
        days: int = 7,
        limit: int = 500
    ) -> List[AuditLog]:
        """
        Find security-critical events.
        
        Args:
            client_id: Client ID
            days: Number of days to look back (default 7)
            limit: Maximum results (default 500)
            
        Returns:
            List of security-critical audit logs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Security-critical event types
            critical_events = [
                AuditEventType.LOGIN_FAILED_ACCOUNT_LOCKED,
                AuditEventType.ACCOUNT_LOCKED,
                AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                AuditEventType.MFA_DISABLED,
                AuditEventType.USER_DELETED_BY_ADMIN,
                AuditEventType.PASSWORD_RESET_COMPLETED,
                AuditEventType.LOGIN_FAILED,
            ]
            
            event_type_values = [et.value for et in critical_events]
            
            query = select(DBAuditLog).where(
                and_(
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= cutoff_date,
                    DBAuditLog.event_type.in_(event_type_values)
                )
            ).order_by(desc(DBAuditLog.created_at)).limit(limit)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
            
        except Exception as e:
            logger.error(f"Error finding security events: {e}", exc_info=True)
            return []
    
    async def count_failed_logins(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        minutes: int = 30
    ) -> int:
        """
        Count failed login attempts.
        
        Used for brute-force detection.
        
        Args:
            user_id: Optional user ID filter
            ip_address: Optional IP address filter
            minutes: Time window in minutes (default 30)
            
        Returns:
            Count of failed login attempts
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            conditions = [
                DBAuditLog.event_type == AuditEventType.LOGIN_FAILED.value,
                DBAuditLog.created_at >= cutoff_time
            ]
            
            if user_id:
                conditions.append(DBAuditLog.user_id == user_id)
            
            if ip_address:
                conditions.append(DBAuditLog.ip_address == ip_address)
            
            query = select(DBAuditLog).where(and_(*conditions))
            
            result = await self.session.execute(query)
            logs = result.scalars().all()
            
            return len(logs)
            
        except Exception as e:
            logger.error(f"Error counting failed logins: {e}", exc_info=True)
            return 0

