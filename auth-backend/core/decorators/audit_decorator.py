"""
Audit Decorator for Automatic Change Tracking
Simplifies audit logging in service methods
"""
from functools import wraps
from typing import Callable, List
import logging

from core.services.audit.audit_service import AuditService
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.entity_change import EntityChange
from core.utils.change_detector import ChangeDetector

logger = logging.getLogger(__name__)


def audit_entity_change(
    event_type: AuditEventType,
    entity_type: str,
    entity_id_param: str = "entity_id",
    entity_name_param: str = "name",
    track_changes: bool = True
):
    """
    Decorator to automatically audit entity changes.
    
    Automatically:
    - Captures old state (for updates)
    - Executes service method
    - Detects field-level changes
    - Logs comprehensive audit event
    
    Usage in service:
        @audit_entity_change(
            event_type=AuditEventType.ENTITY_UPDATED,
            entity_type="project",
            entity_id_param="project_id",
            track_changes=True
        )
        async def update_project(
            self,
            project_id: str,
            data: UpdateProjectRequest,
            current_user: AppUser,
            audit_service: AuditService,  # Required
            repository: IProjectRepository  # Required for change tracking
        ):
            # Service method implementation
            updated = await repository.update(project_id, data)
            return updated
    
    Args:
        event_type: Type of audit event (ENTITY_CREATED, ENTITY_UPDATED, etc.)
        entity_type: Type of entity being changed ("project", "user", etc.)
        entity_id_param: Parameter name for entity ID in function
        entity_name_param: Parameter name for entity name/title in result
        track_changes: Whether to track field-level changes (for updates)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract required dependencies from kwargs
            audit_service: AuditService = kwargs.get('audit_service')
            current_user = kwargs.get('current_user')
            
            if not audit_service:
                # No audit service provided, just execute function normally
                logger.warning(f"Audit decorator on {func.__name__} but no audit_service provided")
                return await func(*args, **kwargs)
            
            # Get entity ID
            entity_id = kwargs.get(entity_id_param)
            
            # For updates/deletes, get old state before operation
            old_entity = None
            if track_changes and event_type in [
                AuditEventType.ENTITY_UPDATED,
                AuditEventType.ENTITY_DELETED
            ]:
                repository = kwargs.get('repository')
                if repository and entity_id:
                    try:
                        # Try to find old entity
                        if hasattr(repository, 'find_by_id'):
                            old_entity = await repository.find_by_id(entity_id)
                    except Exception as e:
                        logger.warning(f"Could not fetch old entity for change tracking: {e}")
            
            # Execute the actual function
            result = await func(*args, **kwargs)
            
            # Extract entity info from result
            entity_name = "Unknown"
            final_entity_id = entity_id
            
            # Try to get entity ID from result if not in params
            if not final_entity_id and result:
                if hasattr(result, 'id'):
                    final_entity_id = result.id
                elif isinstance(result, dict) and 'id' in result:
                    final_entity_id = result['id']
            
            # Try to get entity name
            if result:
                if hasattr(result, entity_name_param):
                    entity_name = getattr(result, entity_name_param)
                elif isinstance(result, dict) and entity_name_param in result:
                    entity_name = result[entity_name_param]
            
            # Detect changes (for updates)
            changes: List[EntityChange] = []
            old_values = None
            new_values = None
            
            if old_entity and result and track_changes:
                try:
                    changes = ChangeDetector.detect_changes(old_entity, result)
                    old_values = ChangeDetector.entity_to_dict(old_entity)
                    new_values = ChangeDetector.entity_to_dict(result)
                except Exception as e:
                    logger.warning(f"Error detecting changes: {e}")
            
            # Extract user info
            user_id = current_user.id if current_user else None
            username = current_user.username if current_user else None
            user_email = current_user.email if current_user and hasattr(current_user, 'email') else None
            client_id = current_user.client_id if current_user else kwargs.get('client_id', 'system')
            
            # Log audit event
            try:
                await audit_service.log_entity_change(
                    client_id=client_id,
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=final_entity_id or "unknown",
                    entity_name=entity_name,
                    changes=changes,
                    user_id=user_id,
                    username=username,
                    old_values=old_values,
                    new_values=new_values,
                    ip_address=kwargs.get('ip_address'),
                    user_agent=kwargs.get('user_agent'),
                    request_id=kwargs.get('request_id'),
                    session_id=kwargs.get('session_id'),
                )
            except Exception as audit_error:
                # Don't fail the operation if audit logging fails
                logger.error(f"Audit decorator error: {audit_error}", exc_info=True)
            
            return result
        
        return wrapper
    return decorator


def audit_data_access(
    access_type: str,  # "view", "download", "export"
    resource_type: str,
    is_sensitive: bool = False
):
    """
    Decorator to automatically audit data access.
    
    Usage:
        @audit_data_access(access_type="view", resource_type="document", is_sensitive=True)
        async def view_sensitive_document(
            self,
            document_id: str,
            current_user: AppUser,
            audit_service: AuditService
        ):
            document = await repository.find_by_id(document_id)
            return document
    
    Args:
        access_type: Type of access ("view", "download", "export")
        resource_type: Type of resource
        is_sensitive: Whether resource contains sensitive data
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            audit_service: AuditService = kwargs.get('audit_service')
            current_user = kwargs.get('current_user')
            
            # Execute function first
            result = await func(*args, **kwargs)
            
            # Log data access (if audit service available)
            if audit_service and current_user and result:
                try:
                    # Extract resource info
                    resource_id = result.id if hasattr(result, 'id') else "unknown"
                    resource_name = "Unknown"
                    
                    if hasattr(result, 'name'):
                        resource_name = result.name
                    elif hasattr(result, 'title'):
                        resource_name = result.title
                    elif isinstance(result, dict):
                        resource_name = result.get('name') or result.get('title') or "Unknown"
                    
                    await audit_service.log_data_access(
                        client_id=current_user.client_id,
                        access_type=access_type,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        resource_name=resource_name,
                        user_id=current_user.id,
                        username=current_user.username,
                        is_sensitive=is_sensitive,
                        ip_address=kwargs.get('ip_address'),
                        user_agent=kwargs.get('user_agent')
                    )
                except Exception as audit_error:
                    logger.error(f"Data access audit error: {audit_error}", exc_info=True)
            
            return result
        
        return wrapper
    return decorator

