"""
Audit Log Routes
Endpoints for viewing audit logs and security events
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional, List
import logging

from app.api.dtos.response.audit_response import (
    AuditLogResponse,
    AuditLogsResponse,
    SecurityEventsResponse
)
from app.api.middlewares.auth_middleware import get_current_user
from app.api.middlewares.authorization import require_admin
from app.api.dicontainer.dicontainer import get_audit_service
from core.domain.auth.app_user import AppUser
from core.domain.auth.audit_event_type import AuditEventType
from core.services.audit.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Audit"])


@router.get("/auth/audit", response_model=AuditLogsResponse)
async def get_user_audit_logs(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    event_types: Optional[List[str]] = Query(None),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """
    Get audit logs for current user.
    
    Shows user's own activity history.
    """
    try:
        event_type_enums = [AuditEventType(et) for et in event_types] if event_types else None
        
        logs = await audit_service.get_user_audit_logs(
            user_id=current_user.id,
            client_id=current_user.client_id,
            event_types=event_type_enums,
            days=days,
            limit=limit
        )
        
        logs_response = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                event_type=log.event_type.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                metadata=log.metadata,
                status=log.status,
                created_at=log.created_at.isoformat() if log.created_at else None
            )
            for log in logs
        ]
        
        return AuditLogsResponse(logs=logs_response, total=len(logs_response))
    except Exception as e:
        logger.error(f"Error getting user audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get audit logs")


@router.get("/admin/audit", response_model=AuditLogsResponse)
async def get_all_audit_logs(
    current_user: Annotated[AppUser, Depends(require_admin)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    event_types: Optional[List[str]] = Query(None),
    limit: Annotated[int, Query(ge=1, le=1000)] = 1000,
):
    """
    Get all audit logs for client (admin only).
    
    Shows all users' activity for this tenant.
    """
    try:
        event_type_enums = [AuditEventType(et) for et in event_types] if event_types else None
        
        logs = await audit_service.get_client_audit_logs(
            client_id=current_user.client_id,
            event_types=event_type_enums,
            days=days,
            limit=limit
        )
        
        logs_response = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                event_type=log.event_type.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                metadata=log.metadata,
                status=log.status,
                created_at=log.created_at.isoformat() if log.created_at else None
            )
            for log in logs
        ]
        
        return AuditLogsResponse(logs=logs_response, total=len(logs_response))
    except Exception as e:
        logger.error(f"Error getting all audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get audit logs")


@router.get("/admin/audit/security", response_model=SecurityEventsResponse)
async def get_security_events(
    current_user: Annotated[AppUser, Depends(require_admin)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    days: Annotated[int, Query(ge=1, le=30)] = 7,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
):
    """
    Get security-critical events (admin only).
    
    Shows:
    - Failed logins
    - Account lockouts
    - Suspicious activity
    - Password resets
    - MFA changes
    """
    try:
        events = await audit_service.get_security_events(
            client_id=current_user.client_id,
            days=days,
            limit=limit
        )
        
        events_response = [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                event_type=log.event_type.value,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                metadata=log.metadata,
                status=log.status,
                created_at=log.created_at.isoformat() if log.created_at else None
            )
            for log in events
        ]
        
        return SecurityEventsResponse(events=events_response, total=len(events_response))
    except Exception as e:
        logger.error(f"Error getting security events: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get security events")

