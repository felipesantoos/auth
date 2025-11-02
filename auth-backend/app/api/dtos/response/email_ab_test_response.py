"""
Email A/B Test Response DTOs
Pydantic models for A/B testing API responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class ABTestVariantMetrics(BaseModel):
    """Metrics for A/B test variant."""
    sent: int = Field(..., description="Total emails sent")
    delivered: int = Field(..., description="Total emails delivered")
    opened: int = Field(..., description="Total emails opened")
    clicked: int = Field(..., description="Total emails clicked")
    bounced: int = Field(..., description="Total emails bounced")


class ABTestVariantRates(BaseModel):
    """Rates for A/B test variant."""
    delivery_rate: str = Field(..., description="Delivery rate percentage")
    open_rate: str = Field(..., description="Open rate percentage")
    click_rate: str = Field(..., description="Click rate percentage")
    ctr: str = Field(..., description="Click-through rate percentage")


class ABTestVariantResponse(BaseModel):
    """Response for A/B test variant data."""
    variant_name: str = Field(..., description="Variant name (A, B, C)")
    template_name: str = Field(..., description="Email template")
    subject: str = Field(..., description="Subject line")
    metrics: ABTestVariantMetrics = Field(..., description="Performance metrics")
    rates: ABTestVariantRates = Field(..., description="Calculated rates")
    is_winner: bool = Field(..., description="Whether this is the winning variant")


class ABTestResponse(BaseModel):
    """Response for A/B test data."""
    test_id: str = Field(..., description="Test ID")
    name: str = Field(..., description="Test name")
    status: str = Field(..., description="Test status (draft, active, paused, completed)")
    start_date: Optional[str] = Field(None, description="Start date (ISO)")
    end_date: Optional[str] = Field(None, description="End date (ISO)")
    winner_variant: Optional[str] = Field(None, description="Winning variant name")
    winner_selected_at: Optional[str] = Field(None, description="Winner selection date (ISO)")
    variants: List[ABTestVariantResponse] = Field(default=[], description="Test variants")


class CreateABTestResponse(BaseModel):
    """Response for A/B test creation."""
    test_id: str = Field(..., description="Created test ID")
    name: str = Field(..., description="Test name")
    status: str = Field(..., description="Test status")
    variant_count: int = Field(..., description="Number of variants")


class AddVariantResponse(BaseModel):
    """Response for variant addition."""
    variant_id: str = Field(..., description="Variant ID")
    variant_name: str = Field(..., description="Variant name")
    template: str = Field(..., description="Template name")
    weight: float = Field(..., description="Distribution weight")


class SendABTestCampaignResponse(BaseModel):
    """Response for A/B test campaign sending."""
    total_sent: int = Field(..., description="Total emails sent")
    successful: int = Field(..., description="Successfully sent")
    failed: int = Field(..., description="Failed to send")
    variants_used: List[str] = Field(..., description="Variants that were used")


class CalculateWinnerResponse(BaseModel):
    """Response for winner calculation."""
    variant_id: str = Field(..., description="Winner variant ID")
    variant_name: str = Field(..., description="Winner variant name")
    template: str = Field(..., description="Winner template")
    metric: str = Field(..., description="Winning metric")
    value: float = Field(..., description="Metric value")


class DeclareWinnerResponse(BaseModel):
    """Response for winner declaration."""
    status: str = Field(..., description="Status (winner_declared)")
    test_id: str = Field(..., description="Test ID")
    winner_variant: str = Field(..., description="Winning variant name")


class StopTestResponse(BaseModel):
    """Response for test stopping."""
    status: str = Field(..., description="Status (stopped)")
    test_id: str = Field(..., description="Test ID")
    end_date: str = Field(..., description="End date (ISO)")

