"""
Comprehensive Audit Log Routes
Advanced endpoints for audit trail, analytics, and compliance
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
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
from core.domain.audit.audit_event_category import AuditEventCategory
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


# ===== Advanced Audit Endpoints =====

class SearchRequest(BaseModel):
    """Audit search request"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 100


@router.get("/audit/entity/{resource_type}/{resource_id}/history")
async def get_entity_history(
    resource_type: str,
    resource_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get complete audit history for an entity.
    
    Shows all events that affected this entity (creates, updates, deletes, views).
    Useful for compliance and debugging.
    
    Example: `/api/audit/entity/project/123/history`
    """
    try:
        logs = await audit_service.get_entity_audit_trail(
            entity_type=resource_type,
            entity_id=resource_id,
            limit=limit
        )
        
        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "history": [
                {
                    "event_id": log.event_id,
                    "event_type": log.event_type.value if log.event_type else None,
                    "event_category": log.event_category.value if log.event_category else None,
                    "action": log.action,
                    "username": log.username,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "success": log.success,
                    "changes": log.changes if log.has_changes() else None,
                    "change_summary": log.get_change_summary() if log.has_changes() else None
                }
                for log in logs
            ],
            "total_events": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting entity history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get entity history")


@router.get("/admin/audit/statistics")
async def get_audit_statistics(
    current_user: Annotated[AppUser, Depends(require_admin)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    days: int = Query(7, ge=1, le=90)
):
    """
    Get audit statistics and analytics (admin only).
    
    Returns:
    - Total events
    - Events by category
    - Top users by activity
    - Success/failure rates
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get statistics from repository
        from app.api.dicontainer.dicontainer import get_audit_log_repository
        repository = await get_audit_log_repository()
        
        stats = await repository.get_statistics(
            client_id=current_user.client_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "statistics": stats,
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/auth/audit/timeline")
async def get_my_activity_timeline(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=90)
):
    """
    Get current user's activity timeline (daily counts).
    
    Returns array of {date, count} for visualization.
    """
    try:
        from app.api.dicontainer.dicontainer import get_audit_log_repository
        repository = await get_audit_log_repository()
        
        timeline = await repository.get_user_activity_timeline(
            user_id=current_user.id,
            days=days
        )
        
        return {
            "user_id": current_user.id,
            "period_days": days,
            "timeline": timeline
        }
    except Exception as e:
        logger.error(f"Error getting activity timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get timeline")


@router.get("/admin/audit/timeline/{user_id}")
async def get_user_activity_timeline(
    user_id: str,
    current_user: Annotated[AppUser, Depends(require_admin)],
    days: int = Query(30, ge=1, le=90)
):
    """
    Get any user's activity timeline (admin only).
    """
    try:
        from app.api.dicontainer.dicontainer import get_audit_log_repository
        repository = await get_audit_log_repository()
        
        timeline = await repository.get_user_activity_timeline(
            user_id=user_id,
            days=days
        )
        
        return {
            "user_id": user_id,
            "period_days": days,
            "timeline": timeline
        }
    except Exception as e:
        logger.error(f"Error getting user timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get timeline")


@router.post("/admin/audit/search")
async def search_audit_logs(
    request: SearchRequest,
    current_user: Annotated[AppUser, Depends(require_admin)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)]
):
    """
    Full-text search in audit logs (admin only).
    
    Searches: action, description, resource_name
    
    Supports filters:
    - user_id
    - resource_type
    - event_category
    - success (true/false)
    - tags (array)
    """
    try:
        # Add client filter
        filters = request.filters or {}
        filters["client_id"] = current_user.client_id
        
        logs = await audit_service.search_audit_logs(
            query=request.query,
            filters=filters,
            limit=request.limit
        )
        
        return {
            "query": request.query,
            "filters": filters,
            "results": [
                {
                    "event_id": log.event_id,
                    "event_type": log.event_type.value if log.event_type else None,
                    "event_category": log.event_category.value if log.event_category else None,
                    "action": log.action,
                    "username": log.username,
                    "resource_type": log.resource_type,
                    "resource_name": log.resource_name,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "success": log.success,
                    "tags": log.tags
                }
                for log in logs
            ],
            "total": len(logs)
        }
    except Exception as e:
        logger.error(f"Error searching audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/admin/audit/retention-report")
async def get_retention_report(
    current_user: Annotated[AppUser, Depends(require_admin)]
):
    """
    Get audit retention policy compliance report (admin only).
    
    Shows how many logs need to be archived based on retention policies.
    """
    try:
        from core.services.audit.audit_retention_service import AuditRetentionService
        from app.api.dicontainer.dicontainer import get_audit_log_repository
        
        repository = await get_audit_log_repository()
        retention_service = AuditRetentionService(repository)
        
        report = await retention_service.get_retention_report(
            client_id=current_user.client_id
        )
        
        return report
    except Exception as e:
        logger.error(f"Error getting retention report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate report")


# ===== Frontend-Compatible Endpoints =====

@router.get("/audit/users/{user_id}")
async def get_user_audit_trail(
    user_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    category: Optional[str] = Query(None),
    event_types: Optional[List[str]] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get audit trail for a specific user.
    
    Users can only see their own logs unless they're admin.
    """
    try:
        # Check permission: user can only see own logs unless admin
        if user_id != current_user.id and not current_user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Can only view your own audit logs")
        
        # Parse category filter
        category_filter = None
        if category:
            try:
                category_filter = AuditEventCategory(category)
            except ValueError:
                pass
        
        # Parse event types
        event_type_enums = None
        if event_types:
            try:
                event_type_enums = [AuditEventType(et) for et in event_types]
            except ValueError:
                pass
        
        # Get logs
        logs = await audit_service.get_user_audit_trail(
            user_id=user_id,
            client_id=current_user.client_id,
            category=category_filter,
            event_types=event_type_enums,
            limit=limit,
            offset=offset
        )
        
        # Format response
        logs_data = [
            {
                "id": log.id,
                "event_id": log.event_id,
                "event_type": log.event_type.value if log.event_type else None,
                "event_category": log.event_category.value if log.event_category else None,
                "action": log.action,
                "description": log.description,
                "user_id": log.user_id,
                "username": log.username,
                "user_email": log.user_email,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "location": log.location,
                "request_id": log.request_id,
                "session_id": log.session_id,
                "changes": log.changes if log.has_changes() else None,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "metadata": log.metadata,
                "tags": log.tags,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
        
        return {
            "logs": logs_data,
            "total": len(logs_data),
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user audit trail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get audit trail")


@router.get("/audit/entities/{resource_type}/{resource_id}")
async def get_entity_audit_trail(
    resource_type: str,
    resource_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get complete audit trail for a specific entity.
    
    Shows all events related to this entity.
    """
    try:
        logs = await audit_service.get_entity_audit_trail(
            entity_type=resource_type,
            entity_id=resource_id,
            limit=limit
        )
        
        logs_data = [
            {
                "id": log.id,
                "event_id": log.event_id,
                "event_type": log.event_type.value if log.event_type else None,
                "event_category": log.event_category.value if log.event_category else None,
                "action": log.action,
                "description": log.description,
                "user_id": log.user_id,
                "username": log.username,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "changes": log.changes if log.has_changes() else None,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "metadata": log.metadata,
                "tags": log.tags,
                "success": log.success,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
        
        return logs_data
    except Exception as e:
        logger.error(f"Error getting entity audit trail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get entity audit trail")


@router.get("/audit/recent")
async def get_recent_events(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get recent audit events.
    
    Regular users see their own events, admins see all events.
    """
    try:
        # Parse category
        category_filter = None
        if category:
            try:
                category_filter = AuditEventCategory(category)
            except ValueError:
                pass
        
        # Get recent events
        if current_user.has_role("admin"):
            # Admin sees all events
            logs = await audit_service.get_recent_events(
                client_id=current_user.client_id,
                category=category_filter,
                limit=limit
            )
        else:
            # Regular user sees only their events
            logs = await audit_service.get_user_audit_logs(
                user_id=current_user.id,
                client_id=current_user.client_id,
                days=7,
                limit=limit
            )
        
        logs_data = [
            {
                "id": log.id,
                "event_id": log.event_id,
                "event_type": log.event_type.value if log.event_type else None,
                "event_category": log.event_category.value if log.event_category else None,
                "action": log.action,
                "user_id": log.user_id,
                "username": log.username,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "changes": log.changes if log.has_changes() else None,
                "metadata": log.metadata,
                "tags": log.tags,
                "success": log.success,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
        
        return logs_data
    except Exception as e:
        logger.error(f"Error getting recent events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get recent events")


@router.get("/audit/search")
async def search_audit_logs_get(
    current_user: Annotated[AppUser, Depends(require_admin)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    query: str = Query(..., min_length=1),
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    event_category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    success: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Search audit logs (admin only).
    
    Full-text search across action, description, and resource names.
    """
    try:
        filters = {"client_id": current_user.client_id}
        
        if user_id:
            filters["user_id"] = user_id
        if resource_type:
            filters["resource_type"] = resource_type
        if event_category:
            filters["event_category"] = event_category
        if tags:
            filters["tags"] = tags
        if success is not None:
            filters["success"] = success
        
        logs = await audit_service.search_audit_logs(
            query=query,
            filters=filters,
            limit=limit
        )
        
        logs_data = [
            {
                "id": log.id,
                "event_id": log.event_id,
                "event_type": log.event_type.value if log.event_type else None,
                "event_category": log.event_category.value if log.event_category else None,
                "action": log.action,
                "user_id": log.user_id,
                "username": log.username,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "resource_name": log.resource_name,
                "ip_address": log.ip_address,
                "changes": log.changes if log.has_changes() else None,
                "metadata": log.metadata,
                "tags": log.tags,
                "success": log.success,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
        
        return logs_data
    except Exception as e:
        logger.error(f"Error searching audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/audit/statistics")
async def get_audit_statistics_v2(
    current_user: Annotated[AppUser, Depends(require_admin)],
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    """
    Get audit statistics for a date range (admin only).
    """
    try:
        from app.api.dicontainer.dicontainer import get_audit_log_repository
        from datetime import datetime
        
        repository = await get_audit_log_repository()
        
        # Parse dates
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        stats = await repository.get_statistics(
            client_id=current_user.client_id,
            start_date=start,
            end_date=end
        )
        
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/audit/users/{user_id}/timeline")
async def get_user_timeline(
    user_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=90)
):
    """
    Get user activity timeline.
    
    Users can only see their own timeline unless they're admin.
    """
    try:
        # Check permission
        if user_id != current_user.id and not current_user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Can only view your own timeline")
        
        from app.api.dicontainer.dicontainer import get_audit_log_repository
        
        repository = await get_audit_log_repository()
        timeline = await repository.get_user_activity_timeline(
            user_id=user_id,
            days=days
        )
        
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get timeline")


@router.get("/audit/users/{user_id}/export")
async def export_user_data(
    user_id: str,
    current_user: Annotated[AppUser, Depends(get_current_user)]
):
    """
    Export all user data for GDPR compliance.
    
    Users can export their own data, admins can export any user's data.
    """
    try:
        # Check permission
        if user_id != current_user.id and not current_user.has_role("admin"):
            raise HTTPException(status_code=403, detail="Can only export your own data")
        
        from app.api.dicontainer.dicontainer import get_audit_service, get_user_repository
        
        audit_service_instance = await get_audit_service()
        user_repository = await get_user_repository()
        
        # Get user data
        user = await user_repository.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get audit logs (all of them)
        logs = await audit_service_instance.get_user_audit_logs(
            user_id=user_id,
            client_id=current_user.client_id,
            days=9999,  # Get all logs
            limit=10000
        )
        
        # Format export data
        export_data = {
            "user_data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "audit_trail": [
                {
                    "event_id": log.event_id,
                    "event_type": log.event_type.value if log.event_type else None,
                    "action": log.action,
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "resource": f"{log.resource_type}/{log.resource_id}" if log.resource_type else None
                }
                for log in logs
            ],
            "total_events": len(logs),
            "export_date": datetime.utcnow().isoformat()
        }
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting user data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export data")

