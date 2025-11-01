"""
Email Tracking Routes
API endpoints for email tracking (opens, clicks, analytics, unsubscribe)

Following Hexagonal Architecture:
- Routes depend only on PRIMARY PORTS (interfaces)
- No direct dependency on infrastructure layer
- Services injected via DI container
"""
import logging
import base64
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, Response, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from core.interfaces.primary.email_tracking_service_interface import IEmailTrackingService
from app.api.dicontainer.dicontainer import get_email_tracking_service
from app.api.dtos.response.email_tracking_response import (
    EmailAnalyticsResponse,
    EmailAnalyticsMetrics,
    EmailAnalyticsFilters,
    EmailPreferencesResponse,
    EmailPreferences,
    UnsubscribeResponse,
    UpdatePreferencesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email-tracking"])


# 1x1 transparent GIF for email open tracking
TRACKING_PIXEL = base64.b64decode(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


@router.get("/track/open/{message_id}")
async def track_email_open(
    message_id: str,
    request: Request,
    tracking_service: IEmailTrackingService = Depends(get_email_tracking_service)
):
    """
    Track email open event via 1x1 transparent pixel.
    
    Args:
        message_id: Email message ID
        request: HTTP request
        tracking_service: Injected email tracking service
        
    Returns:
        1x1 transparent GIF image
    """
    # Track open (service handles errors internally)
    await tracking_service.track_open(message_id)
    
    # Always return tracking pixel (even if tracking fails)
    return Response(
        content=TRACKING_PIXEL,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/track/click/{message_id}")
async def track_email_click(
    message_id: str,
    url: str = Query(..., description="Original URL"),
    request: Request = None,
    tracking_service: IEmailTrackingService = Depends(get_email_tracking_service)
):
    """
    Track email click event and redirect to original URL.
    
    Args:
        message_id: Email message ID
        url: Original URL to redirect to
        request: HTTP request
        tracking_service: Injected email tracking service
        
    Returns:
        Redirect to original URL
    """
    # Track click (service handles errors internally)
    await tracking_service.track_click(
        message_id=message_id,
        url=url,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    # Always redirect (even if tracking fails)
    return RedirectResponse(url=url)


@router.get("/analytics", response_model=EmailAnalyticsResponse)
async def get_email_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    template_name: Optional[str] = None,
    tracking_service: IEmailTrackingService = Depends(get_email_tracking_service)
) -> EmailAnalyticsResponse:
    """
    Get email analytics and metrics.
    
    Args:
        start_date: Filter by start date
        end_date: Filter by end date
        template_name: Filter by template name
        tracking_service: Injected email tracking service
        
    Returns:
        Analytics metrics with filters
    """
    try:
        analytics = await tracking_service.get_analytics(
            start_date=start_date,
            end_date=end_date,
            template_name=template_name
        )
        
        return EmailAnalyticsResponse(
            metrics=EmailAnalyticsMetrics(**analytics),
            filters=EmailAnalyticsFilters(
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                template_name=template_name
            )
        )
    
    except Exception as e:
        logger.error(f"Error getting email analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.post("/unsubscribe", response_model=UnsubscribeResponse)
async def unsubscribe_one_click(
    token: str = Query(..., description="Unsubscribe token"),
    tracking_service: IEmailTrackingService = Depends(get_email_tracking_service)
) -> UnsubscribeResponse:
    """
    One-click unsubscribe (RFC 8058).
    
    Args:
        token: Unsubscribe token
        tracking_service: Injected email tracking service
        
    Returns:
        Unsubscribe status
    """
    try:
        success = await tracking_service.unsubscribe(
            token=token,
            reason="one_click"
        )
        
        if success:
            return UnsubscribeResponse(
                status="unsubscribed",
                message="You have been unsubscribed successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Invalid unsubscribe token")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")


@router.get("/unsubscribe", response_model=EmailPreferencesResponse)
async def get_unsubscribe_preferences(
    token: str = Query(..., description="Unsubscribe token"),
    tracking_service: IEmailTrackingService = Depends(get_email_tracking_service)
) -> EmailPreferencesResponse:
    """
    Get email subscription preferences page.
    
    Args:
        token: Unsubscribe token
        tracking_service: Injected email tracking service
        
    Returns:
        Email preferences
    """
    try:
        preferences_data = await tracking_service.get_preferences(token)
        
        if not preferences_data:
            raise HTTPException(status_code=404, detail="Invalid token")
        
        return EmailPreferencesResponse(
            email=preferences_data["email"],
            preferences=EmailPreferences(**preferences_data["preferences"]),
            unsubscribed_at=preferences_data.get("unsubscribed_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get preferences")


@router.put("/preferences", response_model=UpdatePreferencesResponse)
async def update_email_preferences(
    token: str = Query(..., description="Unsubscribe token"),
    marketing: Optional[bool] = None,
    notifications: Optional[bool] = None,
    updates: Optional[bool] = None,
    newsletter: Optional[bool] = None,
    tracking_service: IEmailTrackingService = Depends(get_email_tracking_service)
) -> UpdatePreferencesResponse:
    """
    Update email subscription preferences.
    
    Args:
        token: Unsubscribe token
        marketing: Receive marketing emails
        notifications: Receive notification emails
        updates: Receive product updates
        newsletter: Receive newsletter
        tracking_service: Injected email tracking service
        
    Returns:
        Updated preferences
    """
    try:
        result = await tracking_service.update_preferences(
            token=token,
            marketing=marketing,
            notifications=notifications,
            updates=updates,
            newsletter=newsletter
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Invalid token")
        
        return UpdatePreferencesResponse(
            status=result["status"],
            preferences=EmailPreferences(**result["preferences"])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update preferences")

