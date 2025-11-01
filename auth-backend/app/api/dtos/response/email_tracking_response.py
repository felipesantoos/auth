"""
Email Tracking Response DTOs
Pydantic models for email tracking API responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict


class EmailAnalyticsMetrics(BaseModel):
    """Email analytics metrics."""
    total_sent: int = Field(..., description="Total emails sent")
    delivered: int = Field(..., description="Total emails delivered")
    delivery_rate: str = Field(..., description="Delivery rate percentage")
    opened: int = Field(..., description="Total emails opened")
    open_rate: str = Field(..., description="Open rate percentage")
    clicked: int = Field(..., description="Total emails with clicks")
    click_rate: str = Field(..., description="Click rate percentage")
    bounced: int = Field(..., description="Total emails bounced")
    bounce_rate: str = Field(..., description="Bounce rate percentage")
    spam_complaints: int = Field(default=0, description="Total spam complaints")


class EmailAnalyticsFilters(BaseModel):
    """Filters applied to analytics query."""
    start_date: Optional[str] = Field(None, description="Start date (ISO)")
    end_date: Optional[str] = Field(None, description="End date (ISO)")
    template_name: Optional[str] = Field(None, description="Template name filter")


class EmailAnalyticsResponse(BaseModel):
    """Response for email analytics endpoint."""
    metrics: EmailAnalyticsMetrics = Field(..., description="Analytics metrics")
    filters: EmailAnalyticsFilters = Field(..., description="Applied filters")


class EmailPreferences(BaseModel):
    """Email subscription preferences."""
    marketing: bool = Field(..., description="Receive marketing emails")
    notifications: bool = Field(..., description="Receive notification emails")
    updates: bool = Field(..., description="Receive product updates")
    newsletter: bool = Field(..., description="Receive newsletter")


class EmailPreferencesResponse(BaseModel):
    """Response for email preferences endpoint."""
    email: str = Field(..., description="Email address")
    preferences: EmailPreferences = Field(..., description="Email preferences")
    unsubscribed_at: Optional[str] = Field(None, description="Unsubscribed timestamp (ISO)")


class UnsubscribeResponse(BaseModel):
    """Response for unsubscribe endpoint."""
    status: str = Field(..., description="Status (unsubscribed)")
    message: str = Field(..., description="Success message")


class UpdatePreferencesResponse(BaseModel):
    """Response for update preferences endpoint."""
    status: str = Field(..., description="Status (updated)")
    preferences: EmailPreferences = Field(..., description="Updated preferences")

