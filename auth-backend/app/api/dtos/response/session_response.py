"""
Session Response DTOs
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SessionInfoResponse(BaseModel):
    """Response for single session info"""
    id: str = Field(..., description="Session ID")
    device_name: str = Field(..., description="Device name/description")
    device_type: Optional[str] = Field(None, description="Device type (mobile/desktop/tablet)")
    ip_address: Optional[str] = Field(None, description="IP address")
    location: Optional[str] = Field(None, description="Location (City, Country)")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp (ISO)")
    created_at: Optional[str] = Field(None, description="Session created timestamp (ISO)")
    is_current: bool = Field(False, description="Whether this is the current session")


class ActiveSessionsResponse(BaseModel):
    """Response for active sessions list"""
    sessions: List[SessionInfoResponse] = Field(..., description="List of active sessions")
    total: int = Field(..., description="Total number of active sessions")


class RevokeSessionResponse(BaseModel):
    """Response for session revoke"""
    success: bool = Field(..., description="Session revoked successfully")
    message: str = Field(default="Session revoked successfully")


class RevokeAllSessionsResponse(BaseModel):
    """Response for revoke all sessions"""
    success: bool = Field(..., description="All sessions revoked")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")
    message: str = Field(default="All sessions revoked successfully")

