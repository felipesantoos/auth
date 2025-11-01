"""
Email A/B Test Database Model
SQLAlchemy model for email A/B testing campaigns
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from infra.database.database import Base
import uuid


class DBEmailABTest(Base):
    """
    SQLAlchemy model for email A/B testing.
    
    Manages A/B test campaigns with multiple variants and winner selection.
    """
    __tablename__ = "email_ab_tests"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Test details
    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Test configuration
    distribution_type = Column(String(20), nullable=False, default="equal")  # 'equal', 'weighted'
    variant_count = Column(Integer, nullable=False, default=2)  # Number of variants (2=A/B, 3=A/B/C)
    
    # Test status
    status = Column(String(20), nullable=False, default="draft")  # 'draft', 'active', 'paused', 'completed'
    
    # Winner selection
    winner_variant = Column(String(10), nullable=True)  # 'A', 'B', 'C', etc
    winner_metric = Column(String(20), nullable=True)  # 'open_rate', 'click_rate', 'conversion_rate'
    auto_select_winner = Column(String, nullable=False, default=False)  # Automatically select winner
    
    # Sample size and confidence
    min_sample_size = Column(Integer, nullable=False, default=100)  # Minimum emails per variant
    confidence_level = Column(Integer, nullable=False, default=95)  # 95% confidence
    
    # Dates
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    winner_selected_at = Column(DateTime, nullable=True)
    
    # Metadata
    test_metadata = Column(JSONB, nullable=True)  # Additional test configuration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    variants = relationship("DBEmailABVariant", back_populates="ab_test", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_ab_test_status', 'status'),
        Index('idx_ab_test_dates', 'start_date', 'end_date'),
    )

