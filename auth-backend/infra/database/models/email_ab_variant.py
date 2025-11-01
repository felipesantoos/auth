"""
Email A/B Test Variant Database Model
SQLAlchemy model for A/B test email variants
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBEmailABVariant(Base):
    """
    SQLAlchemy model for A/B test email variants.
    
    Represents a single variant (A, B, C, etc) in an A/B test.
    """
    __tablename__ = "email_ab_variants"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Foreign key to A/B test
    ab_test_id = Column(String, ForeignKey("email_ab_tests.id"), nullable=False, index=True)
    
    # Variant details
    variant_name = Column(String(10), nullable=False)  # 'A', 'B', 'C', etc
    template_name = Column(String(100), nullable=False)  # Email template to use
    subject_template = Column(String(500), nullable=False)  # Subject line
    
    # Distribution weight (for weighted distribution)
    weight = Column(Float, nullable=False, default=1.0)  # 0.5 = 50%, 1.0 = 100%
    
    # Performance metrics
    sent_count = Column(Integer, nullable=False, default=0)
    delivered_count = Column(Integer, nullable=False, default=0)
    opened_count = Column(Integer, nullable=False, default=0)
    clicked_count = Column(Integer, nullable=False, default=0)
    bounced_count = Column(Integer, nullable=False, default=0)
    
    # Calculated rates (updated periodically)
    delivery_rate = Column(Float, nullable=True)  # delivered/sent
    open_rate = Column(Float, nullable=True)  # opened/delivered
    click_rate = Column(Float, nullable=True)  # clicked/delivered
    ctr = Column(Float, nullable=True)  # Click-through rate (clicked/opened)
    
    # Winner indicators
    is_winner = Column(String, nullable=False, default=False)
    
    # Template context (variables for rendering)
    context = Column(JSONB, nullable=True)  # Template variables specific to this variant
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    ab_test = relationship("DBEmailABTest", back_populates="variants")
    
    # Indexes
    __table_args__ = (
        Index('idx_ab_variant_test', 'ab_test_id', 'variant_name'),
    )

