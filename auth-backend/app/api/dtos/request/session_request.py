"""
Session Request DTOs
"""
from pydantic import BaseModel


class RevokeSessionRequest(BaseModel):
    """Request to revoke specific session (ID in path)"""
    pass


class RevokeAllSessionsRequest(BaseModel):
    """Request to revoke all sessions"""
    except_current: bool = True  # Keep current session active by default

