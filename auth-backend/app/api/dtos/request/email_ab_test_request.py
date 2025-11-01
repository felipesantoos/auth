"""
Email A/B Test Request DTOs
Pydantic models for A/B testing API requests
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class CreateABTestRequest(BaseModel):
    """Request to create A/B test."""
    name: str = Field(..., min_length=1, max_length=200, description="Test name")
    description: Optional[str] = Field(None, max_length=1000, description="Test description")
    variant_count: int = Field(2, ge=2, le=5, description="Number of variants")
    min_sample_size: int = Field(100, ge=10, description="Minimum emails per variant")
    confidence_level: int = Field(95, ge=90, le=99, description="Statistical confidence level")


class AddVariantRequest(BaseModel):
    """Request to add variant to A/B test."""
    variant_name: str = Field(..., min_length=1, max_length=10, description="Variant name (A, B, C)")
    template_name: str = Field(..., min_length=1, description="Email template to use")
    subject_template: str = Field(..., min_length=1, max_length=500, description="Subject line")
    weight: float = Field(1.0, ge=0, le=1, description="Distribution weight (0.5 = 50%)")
    context: Optional[Dict] = Field(None, description="Template variables for this variant")


class SendABTestCampaignRequest(BaseModel):
    """Request to send A/B test campaign."""
    recipients: List[str] = Field(..., min_items=1, description="Email addresses")
    base_context: Optional[Dict] = Field(None, description="Shared context for all variants")


class DeclareWinnerRequest(BaseModel):
    """Request to declare A/B test winner."""
    variant_name: str = Field(..., description="Winning variant name")
    metric: Optional[str] = Field("open_rate", description="Winning metric")

