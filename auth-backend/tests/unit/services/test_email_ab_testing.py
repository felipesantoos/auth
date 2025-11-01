"""
Unit tests for Email A/B Testing
Tests A/B test creation, variant distribution, and winner selection
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.services.email.email_ab_test_service import EmailABTestService
from infra.database.models.email_ab_test import DBEmailABTest
from infra.database.models.email_ab_variant import DBEmailABVariant


@pytest.fixture
def ab_test_service():
    """Create A/B test service for testing."""
    mock_repo = Mock()
    mock_email_service = Mock()
    
    service = EmailABTestService(
        ab_test_repository=mock_repo,
        email_service=mock_email_service
    )
    
    service.ab_test_repo = mock_repo
    service.email_service = mock_email_service
    
    return service


@pytest.mark.asyncio
async def test_create_ab_test(ab_test_service):
    """Test creating A/B test."""
    mock_test = DBEmailABTest(
        id="test-123",
        name="Test Campaign",
        variant_count=2,
        status="draft"
    )
    
    ab_test_service.ab_test_repo.create = AsyncMock(return_value=mock_test)
    
    result = await ab_test_service.create_test(
        name="Test Campaign",
        variant_count=2
    )
    
    assert result["test_id"] == "test-123"
    assert result["status"] == "draft"


@pytest.mark.asyncio
async def test_add_variant(ab_test_service):
    """Test adding variant to A/B test."""
    mock_variant = DBEmailABVariant(
        id="variant-123",
        ab_test_id="test-123",
        variant_name="A",
        template_name="welcome",
        subject_template="Welcome!",
        weight=1.0
    )
    
    ab_test_service.ab_test_repo.create_variant = AsyncMock(return_value=mock_variant)
    
    result = await ab_test_service.add_variant(
        test_id="test-123",
        variant_name="A",
        template_name="welcome",
        subject_template="Welcome!"
    )
    
    assert result["variant_name"] == "A"
    assert result["template"] == "welcome"


@pytest.mark.asyncio
async def test_start_test(ab_test_service):
    """Test starting A/B test."""
    mock_test = DBEmailABTest(
        id="test-123",
        name="Test",
        status="draft"
    )
    
    mock_variants = [
        DBEmailABVariant(id="v1", variant_name="A", ab_test_id="test-123"),
        DBEmailABVariant(id="v2", variant_name="B", ab_test_id="test-123")
    ]
    
    ab_test_service.ab_test_repo.get_by_id = AsyncMock(return_value=mock_test)
    ab_test_service.ab_test_repo.get_variants_by_test = AsyncMock(return_value=mock_variants)
    ab_test_service.ab_test_repo.update = AsyncMock(return_value=mock_test)
    
    success = await ab_test_service.start_test("test-123")
    
    assert success is True
    assert mock_test.status == "active"


@pytest.mark.asyncio
async def test_calculate_winner(ab_test_service):
    """Test calculating A/B test winner."""
    variant_a = DBEmailABVariant(
        id="v1",
        variant_name="A",
        sent_count=100,
        delivered_count=98,
        opened_count=50,
        open_rate=0.51  # 51% open rate
    )
    
    variant_b = DBEmailABVariant(
        id="v2",
        variant_name="B",
        sent_count=100,
        delivered_count=97,
        opened_count=40,
        open_rate=0.41  # 41% open rate
    )
    
    ab_test_service.ab_test_repo.calculate_winner = AsyncMock(return_value=variant_a)
    
    winner = await ab_test_service.calculate_winner("test-123", "open_rate")
    
    assert winner is not None
    assert winner["variant_name"] == "A"


@pytest.mark.asyncio
async def test_declare_winner(ab_test_service):
    """Test declaring A/B test winner."""
    mock_test = DBEmailABTest(
        id="test-123",
        name="Test",
        status="active"
    )
    
    mock_variants = [
        DBEmailABVariant(id="v1", variant_name="A", ab_test_id="test-123"),
        DBEmailABVariant(id="v2", variant_name="B", ab_test_id="test-123")
    ]
    
    ab_test_service.ab_test_repo.get_by_id = AsyncMock(return_value=mock_test)
    ab_test_service.ab_test_repo.get_variants_by_test = AsyncMock(return_value=mock_variants)
    ab_test_service.ab_test_repo.update = AsyncMock(return_value=mock_test)
    ab_test_service.ab_test_repo.update_variant = AsyncMock()
    
    success = await ab_test_service.declare_winner("test-123", "A")
    
    assert success is True
    assert mock_test.winner_variant == "A"
    assert mock_test.status == "completed"


@pytest.mark.asyncio
async def test_stop_test(ab_test_service):
    """Test stopping A/B test."""
    mock_test = DBEmailABTest(
        id="test-123",
        name="Test",
        status="active"
    )
    
    ab_test_service.ab_test_repo.get_by_id = AsyncMock(return_value=mock_test)
    ab_test_service.ab_test_repo.update = AsyncMock(return_value=mock_test)
    
    success = await ab_test_service.stop_test("test-123")
    
    assert success is True
    assert mock_test.status == "paused"
    assert mock_test.end_date is not None

