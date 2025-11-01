"""
Audit Log Response DTOs
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AuditLogResponse(BaseModel):
    """Response for single audit log entry"""
    id: str = Field(..., description="Audit log ID")
    user_id: Optional[str] = Field(None, description="User ID (if authenticated)")
    event_type: str = Field(..., description="Event type")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event data")
    status: str = Field(..., description="Event status (success/failure)")
    created_at: str = Field(..., description="Event timestamp (ISO)")


class AuditLogsResponse(BaseModel):
    """Response for audit logs list"""
    logs: List[AuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of logs")


class SecurityEventsResponse(BaseModel):
    """Response for security events"""
    events: List[AuditLogResponse] = Field(..., description="Security-critical events")
    total: int = Field(..., description="Total number of events")

