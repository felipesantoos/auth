"""
Comprehensive Audit Service
Enterprise-grade audit logging for compliance, security, and analytics
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory
from core.domain.audit.entity_change import EntityChange
from core.interfaces.secondary.audit_log_repository_interface import IAuditLogRepository
from core.exceptions import DomainException

logger = logging.getLogger(__name__)


class AuditService:
    """
    Comprehensive audit service for tracking all system events.
    
    Provides specialized methods for logging different types of events:
    - General events (authentication, authorization)
    - Entity changes (CRUD with before/after tracking)
    - Data access (views, downloads, exports)
    - Business logic events (workflows, approvals)
    - Administrative actions (user management, settings)
    
    Features:
    - Field-level change tracking
    - Compliance tagging (GDPR, SOX, HIPAA)
    - Automatic categorization
    - Security event detection
    """
    
    def __init__(self, repository: IAuditLogRepository):
        self.repository = repository
    
    async def log_event(
        self,
        client_id: str,
        event_type: AuditEventType,
        action: str = "",
        description: str = "",
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        impersonated_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        status: str = "success"
    ) -> AuditLog:
        """
        Log a general audit event.
        
        This is the main method for logging any audit event.
        Other specialized methods call this internally.
        
        Args:
            client_id: Client (tenant) ID
            event_type: Type of event
            action: Human-readable action description
            description: Detailed description (optional)
            user_id: User who performed action
            username: Username for display
            user_email: User email
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            resource_name: Name/title of resource
            ip_address: Client IP
            user_agent: User agent string
            location: Geolocation
            request_id: Request correlation ID
            session_id: Session ID
            impersonated_by: Admin ID if impersonating
            metadata: Additional context
            tags: Event tags (e.g., ["sensitive", "compliance"])
            success: Whether action was successful
            error_message: Error message if failed
            status: Event status (success/failure/warning)
            
        Returns:
            Created audit log
        """
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                action=action or event_type.value.replace("_", " ").title(),
                description=description,
                user_id=user_id,
                username=username,
                user_email=user_email,
                client_id=client_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                request_id=request_id,
                session_id=session_id,
                impersonated_by=impersonated_by,
                metadata=metadata or {},
                tags=tags or [],
                success=success,
                status=status if status else ("success" if success else "failure"),
                error_message=error_message,
                created_at=datetime.utcnow()
            )
            
            audit_log.validate()
            
            saved_log = await self.repository.save(audit_log)
            
            # Log to application logger
            self._log_to_application_logger(audit_log)
            
            return saved_log
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}", exc_info=True)
            # Don't fail the main operation if audit logging fails
            return AuditLog(
                id=None,
                user_id=user_id,
                client_id=client_id,
                event_type=event_type,
                status="error",
                metadata={"error": str(e)}
            )
    
    async def log_entity_change(
        self,
        client_id: str,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        changes: List[EntityChange],
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log an entity change event (create, update, delete).
        
        Tracks before/after state for compliance and auditing.
        
        Args:
            client_id: Client ID
            event_type: Type of change (ENTITY_CREATED, ENTITY_UPDATED, etc.)
            entity_type: Type of entity ("project", "document", "user", etc.)
            entity_id: Entity ID
            entity_name: Entity name/title for display
            changes: List of EntityChange objects (field-level changes)
            user_id: User who made change
            username: Username
            old_values: Complete old state (optional)
            new_values: Complete new state (optional)
            **kwargs: Additional context (ip_address, user_agent, etc.)
            
        Returns:
            Created audit log
        """
        # Build action description
        action_map = {
            AuditEventType.ENTITY_CREATED: "created",
            AuditEventType.ENTITY_UPDATED: "updated",
            AuditEventType.ENTITY_DELETED: "deleted",
            AuditEventType.ENTITY_RESTORED: "restored",
            AuditEventType.BULK_UPDATE: "bulk updated",
            AuditEventType.BULK_DELETE: "bulk deleted"
        }
        action_verb = action_map.get(event_type, "modified")
        action = f"{action_verb.capitalize()} {entity_type} '{entity_name}'"
        
        # Convert changes to dict format
        changes_dict = [change.to_dict() for change in changes if change.is_significant()]
        
        # Build tags
        tags = kwargs.get("tags", [])
        tags.append("data_modification")
        
        # Mark as critical if deletion
        if event_type in [AuditEventType.ENTITY_DELETED, AuditEventType.BULK_DELETE]:
            tags.append("critical")
        
        # Mark as compliance if has changes
        if len(changes_dict) > 0:
            tags.append("compliance")
        
        return await self.log_event(
            client_id=client_id,
            event_type=event_type,
            action=action,
            user_id=user_id,
            username=username,
            resource_type=entity_type,
            resource_id=entity_id,
            resource_name=entity_name,
            metadata={
                **(kwargs.get("metadata", {})),
                "changes_count": len(changes_dict)
            },
            tags=tags,
            success=kwargs.get("success", True),
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent"),
            request_id=kwargs.get("request_id"),
            session_id=kwargs.get("session_id"),
            **{k: v for k, v in kwargs.items() if k not in ["tags", "metadata", "success", "ip_address", "user_agent", "request_id", "session_id"]}
        )
    
    async def log_data_access(
        self,
        client_id: str,
        access_type: str,  # "view", "download", "export"
        resource_type: str,
        resource_id: str,
        resource_name: str,
        user_id: str,
        username: str,
        is_sensitive: bool = False,
        **kwargs
    ) -> AuditLog:
        """
        Log data access event.
        
        Critical for compliance (GDPR Article 15, HIPAA).
        Tracks who accessed what data and when.
        
        Args:
            client_id: Client ID
            access_type: Type of access ("view", "download", "export")
            resource_type: Resource type
            resource_id: Resource ID
            resource_name: Resource name
            user_id: User who accessed
            username: Username
            is_sensitive: Whether data is sensitive (PII, PHI, financial)
            **kwargs: Additional context
            
        Returns:
            Created audit log
        """
        event_type_map = {
            "view": AuditEventType.ENTITY_VIEWED,
            "download": AuditEventType.FILE_DOWNLOADED,
            "export": AuditEventType.DATA_EXPORTED
        }
        event_type = event_type_map.get(access_type, AuditEventType.ENTITY_VIEWED)
        
        action = f"{access_type.capitalize()}ed {resource_type} '{resource_name}'"
        
        tags = kwargs.get("tags", [])
        tags.append("data_access")
        
        if is_sensitive:
            tags.extend(["sensitive", "compliance", "pii"])
            event_type = AuditEventType.SENSITIVE_DATA_ACCESSED
        
        return await self.log_event(
            client_id=client_id,
            event_type=event_type,
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            tags=tags,
            **kwargs
        )
    
    async def log_business_event(
        self,
        client_id: str,
        event_type: AuditEventType,
        action: str,
        user_id: str,
        username: str,
        related_entities: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log business logic event.
        
        Examples: workflow completed, approval granted, task completed
        
        Args:
            client_id: Client ID
            event_type: Business event type
            action: Action description
            user_id: User who triggered event
            username: Username
            related_entities: Related entities [{"type": "project", "id": "123", "name": "Project A"}]
            **kwargs: Additional context
            
        Returns:
            Created audit log
        """
        tags = kwargs.get("tags", [])
        tags.append("business_event")
        
        metadata = kwargs.get("metadata", {})
        if related_entities:
            metadata["related_entities"] = related_entities
        
        kwargs["metadata"] = metadata
        kwargs["tags"] = tags
        
        return await self.log_event(
            client_id=client_id,
            event_type=event_type,
            action=action,
            user_id=user_id,
            username=username,
            **kwargs
        )
    
    async def log_admin_action(
        self,
        client_id: str,
        event_type: AuditEventType,
        action: str,
        admin_user_id: str,
        admin_username: str,
        target_user_id: Optional[str] = None,
        target_username: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log administrative action.
        
        Examples: user activated, settings changed, feature enabled
        
        Args:
            client_id: Client ID
            event_type: Admin event type
            action: Action description
            admin_user_id: Admin who performed action
            admin_username: Admin username
            target_user_id: Target user (if applicable)
            target_username: Target username
            **kwargs: Additional context
            
        Returns:
            Created audit log
        """
        tags = kwargs.get("tags", [])
        tags.extend(["administrative", "critical"])
        
        metadata = kwargs.get("metadata", {})
        if target_user_id:
            metadata["target_user_id"] = target_user_id
            metadata["target_username"] = target_username
        
        kwargs["metadata"] = metadata
        kwargs["tags"] = tags
        
        return await self.log_event(
            client_id=client_id,
            event_type=event_type,
            action=action,
            user_id=admin_user_id,
            username=admin_username,
            **kwargs
        )
    
    def _log_to_application_logger(self, audit_log: AuditLog) -> None:
        """
        Log audit event to application logger.
        
        Uses appropriate log level based on event criticality.
        """
        log_extra = {
            "event_id": audit_log.event_id,
            "event_type": audit_log.event_type.value if audit_log.event_type else None,
            "event_category": audit_log.event_category.value if audit_log.event_category else None,
            "user_id": audit_log.user_id,
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "success": audit_log.success,
            "client_id": audit_log.client_id
        }
        
        # Determine log level
        if audit_log.is_critical():
            logger.warning(f"AUDIT [CRITICAL]: {audit_log.get_summary()}", extra=log_extra)
        elif audit_log.is_security_critical():
            logger.warning(f"AUDIT [SECURITY]: {audit_log.get_summary()}", extra=log_extra)
        elif not audit_log.success:
            logger.warning(f"AUDIT [FAILED]: {audit_log.get_summary()}", extra=log_extra)
        else:
            logger.info(f"AUDIT: {audit_log.get_summary()}", extra=log_extra)
    
    # ===== Query Methods =====
    
    async def get_user_audit_logs(
        self,
        user_id: str,
        client_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID
            client_id: Optional client filter
            event_types: Optional event type filter
            days: Days to look back
            limit: Maximum results
            
        Returns:
            List of audit logs
        """
        try:
            return await self.repository.find_by_user(
                user_id=user_id,
                client_id=client_id,
                event_types=event_types,
                days=days,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting user audit logs: {e}", exc_info=True)
            return []
    
    async def get_user_audit_trail(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get comprehensive audit trail for user (supports pagination).
        
        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            event_types: Optional event types
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of audit logs
        """
        try:
            return await self.repository.find_by_user_paginated(
                user_id, start_date, end_date, event_types, limit, offset
            )
        except Exception as e:
            logger.error(f"Error getting user audit trail: {e}", exc_info=True)
            return []
    
    async def get_entity_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get complete history of changes for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            limit: Max results
            
        Returns:
            List of audit logs (ordered by date desc)
        """
        try:
            return await self.repository.find_by_entity(entity_type, entity_id, limit)
        except Exception as e:
            logger.error(f"Error getting entity audit trail: {e}", exc_info=True)
            return []
    
    async def get_recent_events(
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
            return await self.repository.find_recent(client_id, category, limit)
        except Exception as e:
            logger.error(f"Error getting recent events: {e}", exc_info=True)
            return []
    
    async def search_audit_logs(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Search audit logs (full-text).
        
        Searches: action, description, resource_name
        
        Args:
            query: Search query
            filters: Additional filters {"user_id": "123", "event_category": "..."}
            limit: Max results
            
        Returns:
            Matching audit logs
        """
        try:
            return await self.repository.search(query, filters, limit)
        except Exception as e:
            logger.error(f"Error searching audit logs: {e}", exc_info=True)
            return []
    
    async def get_client_audit_logs(
        self,
        client_id: str,
        event_types: Optional[List[AuditEventType]] = None,
        days: int = 30,
        limit: int = 1000
    ) -> List[AuditLog]:
        """
        Get audit logs for a client (admin view).
        
        Args:
            client_id: Client ID
            event_types: Optional event type filter
            days: Days to look back
            limit: Maximum results
            
        Returns:
            List of audit logs
        """
        try:
            return await self.repository.find_by_client(
                client_id=client_id,
                event_types=event_types,
                days=days,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting client audit logs: {e}", exc_info=True)
            return []
    
    async def get_security_events(
        self,
        client_id: str,
        days: int = 7,
        limit: int = 500
    ) -> List[AuditLog]:
        """
        Get security-critical events (admin view).
        
        Args:
            client_id: Client ID
            days: Days to look back
            limit: Maximum results
            
        Returns:
            List of security-critical audit logs
        """
        try:
            return await self.repository.find_security_events(
                client_id=client_id,
                days=days,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting security events: {e}", exc_info=True)
            return []
    
    # ===== Security Detection Methods (existing) =====
    
    async def detect_brute_force(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        threshold: int = 5,
        minutes: int = 30
    ) -> bool:
        """Detect brute-force attack attempts"""
        try:
            failed_count = await self.repository.count_failed_logins(
                user_id=user_id,
                ip_address=ip_address,
                minutes=minutes
            )
            
            is_attack = failed_count >= threshold
            
            if is_attack:
                logger.warning(
                    f"Brute-force attack detected - Failed logins: {failed_count}",
                    extra={
                        "user_id": user_id,
                        "ip_address": ip_address,
                        "failed_count": failed_count,
                        "threshold": threshold,
                        "minutes": minutes
                    }
                )
            
            return is_attack
            
        except Exception as e:
            logger.error(f"Error detecting brute-force: {e}", exc_info=True)
            return True  # Fail closed
    
    async def detect_suspicious_activity(
        self,
        user_id: str,
        client_id: str,
        ip_address: str,
        user_agent: str,
        location: Optional[str] = None
    ) -> bool:
        """
        Detect suspicious activity patterns.
        
        DEPRECATED: This method is kept for backward compatibility.
        New code should use SuspiciousActivityDetector service directly.
        
        This method now delegates to SuspiciousActivityDetector.
        """
        try:
            # Delegate to dedicated detector service
            from core.services.auth.suspicious_activity_detector import SuspiciousActivityDetector
            detector = SuspiciousActivityDetector(audit_service=self)
            
            return await detector.detect_suspicious_activity(
                user_id=user_id,
                client_id=client_id,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location
            )
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}", exc_info=True)
            return False
