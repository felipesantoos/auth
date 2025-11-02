"""
Comprehensive Audit Log Repository
Advanced persistence with statistics, search, and analytics
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory
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
    
    async def count_failed_logins_by_ip(
        self,
        ip_address: str,
        client_id: str,
        minutes: int = 30
    ) -> int:
        """
        Count failed login attempts from a specific IP address.
        
        Used for IP-based lockout protection.
        
        Args:
            ip_address: IP address to check
            client_id: Client ID (for multi-tenant isolation)
            minutes: Time window in minutes (default 30)
            
        Returns:
            Count of failed login attempts from this IP
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            query = select(func.count(DBAuditLog.id)).where(
                and_(
                    DBAuditLog.event_type == AuditEventType.LOGIN_FAILED.value,
                    DBAuditLog.ip_address == ip_address,
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= cutoff_time
                )
            )
            
            result = await self.session.execute(query)
            count = result.scalar() or 0
            
            logger.debug(
                f"Found {count} failed login attempts from IP {ip_address} in last {minutes} minutes",
                extra={"ip_address": ip_address, "client_id": client_id, "count": count}
            )
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting failed logins by IP: {e}", exc_info=True)
            return 0
    
    # ===== Advanced Query Methods =====
    
    async def find_by_entity(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get complete history for an entity.
        
        Shows all events that affected this entity (create, updates, deletes, views).
        
        Args:
            resource_type: Type of entity
            resource_id: Entity ID
            limit: Max results
            
        Returns:
            List of audit logs (ordered by date desc)
        """
        try:
            result = await self.session.execute(
                select(DBAuditLog)
                .where(and_(
                    DBAuditLog.resource_type == resource_type,
                    DBAuditLog.resource_id == resource_id
                ))
                .order_by(desc(DBAuditLog.created_at))
                .limit(limit)
            )
            db_logs = result.scalars().all()
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
        except Exception as e:
            logger.error(f"Error finding audit logs by entity: {e}", exc_info=True)
            return []
    
    async def find_by_category(
        self,
        category: AuditEventCategory,
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get events by category.
        
        Args:
            category: Event category
            start_date: Optional start date filter
            limit: Max results
            
        Returns:
            List of audit logs
        """
        try:
            query = select(DBAuditLog).where(DBAuditLog.event_category == category.value)
            
            if start_date:
                query = query.where(DBAuditLog.created_at >= start_date)
            
            query = query.order_by(desc(DBAuditLog.created_at)).limit(limit)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
        except Exception as e:
            logger.error(f"Error finding audit logs by category: {e}", exc_info=True)
            return []
    
    async def find_recent(
        self,
        client_id: Optional[str] = None,
        category: Optional[AuditEventCategory] = None,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get recent audit events.
        
        Args:
            client_id: Optional client filter
            category: Optional category filter
            limit: Max results
            
        Returns:
            List of recent audit logs
        """
        try:
            query = select(DBAuditLog)
            
            conditions = []
            if client_id:
                conditions.append(DBAuditLog.client_id == client_id)
            if category:
                conditions.append(DBAuditLog.event_category == category.value)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(DBAuditLog.created_at)).limit(limit)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
        except Exception as e:
            logger.error(f"Error finding recent audit logs: {e}", exc_info=True)
            return []
    
    async def search(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Full-text search in audit logs.
        
        Searches: action, description, resource_name
        
        Args:
            query_text: Search query
            filters: Additional filters
            limit: Max results
            
        Returns:
            Matching audit logs
        """
        try:
            # Build search query (case-insensitive)
            search_filter = or_(
                DBAuditLog.action.ilike(f"%{query_text}%"),
                DBAuditLog.description.ilike(f"%{query_text}%"),
                DBAuditLog.resource_name.ilike(f"%{query_text}%")
            )
            
            query = select(DBAuditLog).where(search_filter)
            
            # Apply additional filters
            if filters:
                if "user_id" in filters:
                    query = query.where(DBAuditLog.user_id == filters["user_id"])
                
                if "client_id" in filters:
                    query = query.where(DBAuditLog.client_id == filters["client_id"])
                
                if "resource_type" in filters:
                    query = query.where(DBAuditLog.resource_type == filters["resource_type"])
                
                if "event_category" in filters:
                    query = query.where(DBAuditLog.event_category == filters["event_category"])
                
                if "success" in filters:
                    query = query.where(DBAuditLog.success == filters["success"])
                
                if "tags" in filters:
                    # PostgreSQL array contains
                    query = query.where(DBAuditLog.tags.contains(filters["tags"]))
            
            query = query.order_by(desc(DBAuditLog.created_at)).limit(limit)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
        except Exception as e:
            logger.error(f"Error searching audit logs: {e}", exc_info=True)
            return []
    
    async def get_statistics(
        self,
        client_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get audit statistics for date range.
        
        Returns analytics: total events, events by category, top users, success rate.
        
        Args:
            client_id: Client ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Statistics dictionary
        """
        try:
            # Total events
            total_result = await self.session.execute(
                select(func.count(DBAuditLog.id))
                .where(and_(
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= start_date,
                    DBAuditLog.created_at <= end_date
                ))
            )
            total_events = total_result.scalar() or 0
            
            # Events by category
            category_result = await self.session.execute(
                select(
                    DBAuditLog.event_category,
                    func.count(DBAuditLog.id)
                )
                .where(and_(
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= start_date,
                    DBAuditLog.created_at <= end_date
                ))
                .group_by(DBAuditLog.event_category)
            )
            events_by_category = {row[0]: row[1] for row in category_result.all()}
            
            # Top users
            user_result = await self.session.execute(
                select(
                    DBAuditLog.username,
                    func.count(DBAuditLog.id)
                )
                .where(and_(
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= start_date,
                    DBAuditLog.created_at <= end_date,
                    DBAuditLog.username.isnot(None)
                ))
                .group_by(DBAuditLog.username)
                .order_by(desc(func.count(DBAuditLog.id)))
                .limit(10)
            )
            top_users = [{"username": row[0], "count": row[1]} for row in user_result.all()]
            
            # Failed events
            failed_result = await self.session.execute(
                select(func.count(DBAuditLog.id))
                .where(and_(
                    DBAuditLog.client_id == client_id,
                    DBAuditLog.created_at >= start_date,
                    DBAuditLog.created_at <= end_date,
                    DBAuditLog.success == False
                ))
            )
            failed_events = failed_result.scalar() or 0
            
            # Success rate
            success_rate = ((total_events - failed_events) / total_events * 100) if total_events > 0 else 0
            
            return {
                "total_events": total_events,
                "events_by_category": events_by_category,
                "top_users": top_users,
                "failed_events": failed_events,
                "success_events": total_events - failed_events,
                "success_rate": round(success_rate, 2),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}", exc_info=True)
            return {}
    
    async def get_user_activity_timeline(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user activity timeline (daily counts).
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of {date, count} for each day
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.session.execute(
                select(
                    func.date(DBAuditLog.created_at).label('date'),
                    func.count(DBAuditLog.id).label('count')
                )
                .where(and_(
                    DBAuditLog.user_id == user_id,
                    DBAuditLog.created_at >= start_date
                ))
                .group_by(func.date(DBAuditLog.created_at))
                .order_by('date')
            )
            
            return [
                {"date": row.date.isoformat(), "count": row.count}
                for row in result.all()
            ]
        except Exception as e:
            logger.error(f"Error getting user activity timeline: {e}", exc_info=True)
            return []
    
    async def find_by_user_paginated(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get user audit trail with pagination support"""
        try:
            query = select(DBAuditLog).where(DBAuditLog.user_id == user_id)
            
            if start_date:
                query = query.where(DBAuditLog.created_at >= start_date)
            
            if end_date:
                query = query.where(DBAuditLog.created_at <= end_date)
            
            if event_types:
                event_values = [et.value for et in event_types]
                query = query.where(DBAuditLog.event_type.in_(event_values))
            
            query = query.order_by(desc(DBAuditLog.created_at)).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            db_logs = result.scalars().all()
            return [self.mapper.to_domain(db_log) for db_log in db_logs]
        except Exception as e:
            logger.error(f"Error finding user audit trail: {e}", exc_info=True)
            return []
    
    # ===== GDPR & Compliance Methods =====
    
    async def anonymize_user_logs(
        self,
        user_id: str,
        replacement_username: str = "[USER DELETED]",
        replacement_email: str = "deleted@example.com"
    ) -> int:
        """
        Anonymize user data in audit logs (GDPR Article 17 - Right to be Forgotten).
        
        Replaces PII with anonymous placeholders while keeping audit trail intact.
        
        Args:
            user_id: User ID to anonymize
            replacement_username: Replacement username
            replacement_email: Replacement email
            
        Returns:
            Number of logs anonymized
        """
        try:
            stmt = update(DBAuditLog).where(
                DBAuditLog.user_id == user_id
            ).values(
                username=replacement_username,
                user_email=replacement_email,
                # Keep user_id for referential integrity
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            count = result.rowcount
            logger.info(f"Anonymized {count} audit logs for user {user_id}")
            
            return count
        except Exception as e:
            logger.error(f"Error anonymizing user audit logs: {e}", exc_info=True)
            await self.session.rollback()
            return 0
    
    async def save_batch(self, audit_logs: List[AuditLog]) -> List[AuditLog]:
        """
        Save multiple audit logs in batch (for performance).
        
        Args:
            audit_logs: List of audit logs to save
            
        Returns:
            List of saved audit logs
        """
        try:
            db_logs = [self.mapper.to_database(log) for log in audit_logs]
            self.session.add_all(db_logs)
            await self.session.commit()
            
            return audit_logs
        except Exception as e:
            logger.error(f"Error saving audit logs batch: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def count_logs(
        self,
        category: Optional[AuditEventCategory] = None,
        before_date: Optional[datetime] = None,
        client_id: Optional[str] = None
    ) -> int:
        """
        Count audit logs (for retention reporting).
        
        Args:
            category: Optional category filter
            before_date: Count logs before this date
            client_id: Optional client filter
            
        Returns:
            Count of matching logs
        """
        try:
            query = select(func.count(DBAuditLog.id))
            
            conditions = []
            if category:
                conditions.append(DBAuditLog.event_category == category.value)
            if before_date:
                conditions.append(DBAuditLog.created_at < before_date)
            if client_id:
                conditions.append(DBAuditLog.client_id == client_id)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting audit logs: {e}", exc_info=True)
            return 0
    
    async def delete_old_logs(
        self,
        category: AuditEventCategory,
        before_date: datetime
    ) -> int:
        """
        Delete old audit logs (for archival).
        
        WARNING: Only call after successfully archiving logs to S3/cold storage!
        
        Args:
            category: Category to delete
            before_date: Delete logs before this date
            
        Returns:
            Number of logs deleted
        """
        try:
            from sqlalchemy import delete as sql_delete
            
            stmt = sql_delete(DBAuditLog).where(and_(
                DBAuditLog.event_category == category.value,
                DBAuditLog.created_at < before_date
            ))
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            count = result.rowcount
            logger.warning(f"Deleted {count} old audit logs for category {category.value}")
            
            return count
        except Exception as e:
            logger.error(f"Error deleting old audit logs: {e}", exc_info=True)
            await self.session.rollback()
            return 0

