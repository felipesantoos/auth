"""
Integration tests for Email Tracking
Tests email tracking routes and functionality
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
from infra.database.repositories.email_subscription_repository import EmailSubscriptionRepository


@pytest.mark.asyncio
async def test_track_email_open(client: AsyncClient, db: AsyncSession):
    """Test email open tracking endpoint."""
    # Create tracking record
    tracking_repo = EmailTrackingRepository(db)
    tracking = await tracking_repo.create({
        "message_id": "test-message-123",
        "email": "test@example.com",
        "subject": "Test Email",
        "sent_at": "2024-11-01T12:00:00"
    })
    await db.commit()
    
    # Track open
    response = await client.get(f"/api/email/track/open/{tracking.message_id}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    
    # Verify tracking was updated
    await db.refresh(tracking)
    assert tracking.open_count == 1
    assert tracking.opened_at is not None


@pytest.mark.asyncio
async def test_track_email_click(client: AsyncClient, db: AsyncSession):
    """Test email click tracking endpoint."""
    # Create tracking record
    tracking_repo = EmailTrackingRepository(db)
    tracking = await tracking_repo.create({
        "message_id": "test-message-456",
        "email": "test@example.com",
        "subject": "Test Email",
        "sent_at": "2024-11-01T12:00:00"
    })
    await db.commit()
    
    # Track click
    response = await client.get(
        f"/api/email/track/click/{tracking.message_id}?url=https://example.com"
    )
    
    assert response.status_code in [200, 307]  # Redirect
    
    # Verify tracking was updated
    await db.refresh(tracking)
    assert tracking.click_count == 1
    assert tracking.first_click_at is not None


@pytest.mark.asyncio
async def test_get_email_analytics(client: AsyncClient, db: AsyncSession):
    """Test email analytics endpoint."""
    # Create some tracking records
    tracking_repo = EmailTrackingRepository(db)
    
    for i in range(5):
        await tracking_repo.create({
            "message_id": f"test-message-{i}",
            "email": "test@example.com",
            "subject": f"Test Email {i}",
            "sent_at": "2024-11-01T12:00:00",
            "delivered_at": "2024-11-01T12:01:00" if i < 4 else None,
            "opened_at": "2024-11-01T12:02:00" if i < 3 else None
        })
    
    await db.commit()
    
    # Get analytics
    response = await client.get("/api/email/analytics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    assert data["metrics"]["total_sent"] == 5
    assert data["metrics"]["delivered"] == 4
    assert data["metrics"]["opened"] == 3


@pytest.mark.asyncio
async def test_unsubscribe_one_click(client: AsyncClient, db: AsyncSession):
    """Test one-click unsubscribe endpoint."""
    # Create subscription
    subscription_repo = EmailSubscriptionRepository(db)
    subscription = await subscription_repo.create({
        "email": "test@example.com",
        "unsubscribe_token": "test-token-123",
        "marketing_emails": True,
        "notification_emails": True
    })
    await db.commit()
    
    # Unsubscribe
    response = await client.post(f"/api/email/unsubscribe?token={subscription.unsubscribe_token}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsubscribed"
    
    # Verify subscription was updated
    await db.refresh(subscription)
    assert subscription.marketing_emails is False
    assert subscription.notification_emails is False
    assert subscription.unsubscribed_at is not None


@pytest.mark.asyncio
async def test_get_unsubscribe_preferences(client: AsyncClient, db: AsyncSession):
    """Test get unsubscribe preferences endpoint."""
    # Create subscription
    subscription_repo = EmailSubscriptionRepository(db)
    subscription = await subscription_repo.create({
        "email": "test@example.com",
        "unsubscribe_token": "test-token-456",
        "marketing_emails": True,
        "notification_emails": False
    })
    await db.commit()
    
    # Get preferences
    response = await client.get(f"/api/email/unsubscribe?token={subscription.unsubscribe_token}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == "test@example.com"
    assert data["preferences"]["marketing"] is True
    assert data["preferences"]["notifications"] is False


@pytest.mark.asyncio
async def test_update_email_preferences(client: AsyncClient, db: AsyncSession):
    """Test update email preferences endpoint."""
    # Create subscription
    subscription_repo = EmailSubscriptionRepository(db)
    subscription = await subscription_repo.create({
        "email": "test@example.com",
        "unsubscribe_token": "test-token-789",
        "marketing_emails": True,
        "notification_emails": True
    })
    await db.commit()
    
    # Update preferences
    response = await client.put(
        f"/api/email/preferences?token={subscription.unsubscribe_token}&marketing=false&notifications=true"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "updated"
    assert data["preferences"]["marketing"] is False
    assert data["preferences"]["notifications"] is True

