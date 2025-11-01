"""
Email A/B Test Repository
Data access layer for email A/B testing operations
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.email_ab_test import DBEmailABTest
from infra.database.models.email_ab_variant import DBEmailABVariant
import random


class EmailABTestRepository:
    """Repository for email A/B test database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, test_data: dict) -> DBEmailABTest:
        """
        Create new A/B test.
        
        Args:
            test_data: A/B test data
            
        Returns:
            Created A/B test record
        """
        ab_test = DBEmailABTest(**test_data)
        self.session.add(ab_test)
        await self.session.flush()
        return ab_test
    
    async def get_by_id(self, test_id: str) -> Optional[DBEmailABTest]:
        """Get A/B test by ID."""
        result = await self.session.execute(
            select(DBEmailABTest).where(DBEmailABTest.id == test_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_tests(self) -> List[DBEmailABTest]:
        """Get all active A/B tests."""
        result = await self.session.execute(
            select(DBEmailABTest)
            .where(DBEmailABTest.status == "active")
            .where(DBEmailABTest.end_date.is_(None) | (DBEmailABTest.end_date > datetime.utcnow()))
        )
        return result.scalars().all()
    
    async def update(self, ab_test: DBEmailABTest) -> DBEmailABTest:
        """Update A/B test record."""
        self.session.add(ab_test)
        await self.session.flush()
        return ab_test
    
    async def create_variant(self, variant_data: dict) -> DBEmailABVariant:
        """
        Create variant for A/B test.
        
        Args:
            variant_data: Variant data
            
        Returns:
            Created variant record
        """
        variant = DBEmailABVariant(**variant_data)
        self.session.add(variant)
        await self.session.flush()
        return variant
    
    async def get_variant(self, variant_id: str) -> Optional[DBEmailABVariant]:
        """Get variant by ID."""
        result = await self.session.execute(
            select(DBEmailABVariant).where(DBEmailABVariant.id == variant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_variants_by_test(self, test_id: str) -> List[DBEmailABVariant]:
        """Get all variants for a test."""
        result = await self.session.execute(
            select(DBEmailABVariant)
            .where(DBEmailABVariant.ab_test_id == test_id)
            .order_by(DBEmailABVariant.variant_name)
        )
        return result.scalars().all()
    
    async def update_variant(self, variant: DBEmailABVariant) -> DBEmailABVariant:
        """Update variant record."""
        self.session.add(variant)
        await self.session.flush()
        return variant
    
    async def increment_variant_metrics(
        self,
        variant_id: str,
        sent: int = 0,
        delivered: int = 0,
        opened: int = 0,
        clicked: int = 0,
        bounced: int = 0
    ) -> bool:
        """
        Increment variant performance metrics.
        
        Args:
            variant_id: Variant ID
            sent: Increment sent count
            delivered: Increment delivered count
            opened: Increment opened count
            clicked: Increment clicked count
            bounced: Increment bounced count
            
        Returns:
            True if updated successfully
        """
        variant = await self.get_variant(variant_id)
        if not variant:
            return False
        
        variant.sent_count += sent
        variant.delivered_count += delivered
        variant.opened_count += opened
        variant.clicked_count += clicked
        variant.bounced_count += bounced
        
        # Recalculate rates
        if variant.sent_count > 0:
            variant.delivery_rate = variant.delivered_count / variant.sent_count
        
        if variant.delivered_count > 0:
            variant.open_rate = variant.opened_count / variant.delivered_count
            variant.click_rate = variant.clicked_count / variant.delivered_count
        
        if variant.opened_count > 0:
            variant.ctr = variant.clicked_count / variant.opened_count
        
        await self.update_variant(variant)
        return True
    
    async def calculate_winner(
        self,
        test_id: str,
        metric: str = "open_rate"
    ) -> Optional[DBEmailABVariant]:
        """
        Calculate winner based on specified metric.
        
        Args:
            test_id: A/B test ID
            metric: Metric to compare ('open_rate', 'click_rate', 'ctr')
            
        Returns:
            Winning variant or None if not enough data
        """
        variants = await self.get_variants_by_test(test_id)
        
        if not variants:
            return None
        
        # Check if minimum sample size met
        ab_test = await self.get_by_id(test_id)
        if not ab_test:
            return None
        
        for variant in variants:
            if variant.sent_count < ab_test.min_sample_size:
                return None  # Not enough data yet
        
        # Find variant with best metric
        metric_map = {
            "open_rate": lambda v: v.open_rate or 0,
            "click_rate": lambda v: v.click_rate or 0,
            "ctr": lambda v: v.ctr or 0,
            "delivery_rate": lambda v: v.delivery_rate or 0
        }
        
        metric_func = metric_map.get(metric, lambda v: v.open_rate or 0)
        winner = max(variants, key=metric_func)
        
        # Simple statistical significance check
        # (In production, use proper statistical tests like chi-square)
        winner_value = metric_func(winner)
        
        # Check if winner is significantly better (>5% improvement)
        for variant in variants:
            if variant.id != winner.id:
                variant_value = metric_func(variant)
                if winner_value < variant_value * 1.05:
                    return None  # Not statistically significant
        
        return winner
    
    async def get_test_results(self, test_id: str) -> Dict:
        """
        Get comprehensive results for A/B test.
        
        Args:
            test_id: A/B test ID
            
        Returns:
            Dict with test results and statistics
        """
        ab_test = await self.get_by_id(test_id)
        if not ab_test:
            return {}
        
        variants = await self.get_variants_by_test(test_id)
        
        variant_results = []
        for variant in variants:
            variant_results.append({
                "variant_name": variant.variant_name,
                "template_name": variant.template_name,
                "subject": variant.subject_template,
                "metrics": {
                    "sent": variant.sent_count,
                    "delivered": variant.delivered_count,
                    "opened": variant.opened_count,
                    "clicked": variant.clicked_count,
                    "bounced": variant.bounced_count,
                },
                "rates": {
                    "delivery_rate": f"{(variant.delivery_rate * 100):.1f}%" if variant.delivery_rate else "0%",
                    "open_rate": f"{(variant.open_rate * 100):.1f}%" if variant.open_rate else "0%",
                    "click_rate": f"{(variant.click_rate * 100):.1f}%" if variant.click_rate else "0%",
                    "ctr": f"{(variant.ctr * 100):.1f}%" if variant.ctr else "0%",
                },
                "is_winner": variant.is_winner
            })
        
        return {
            "test_id": ab_test.id,
            "name": ab_test.name,
            "status": ab_test.status,
            "start_date": ab_test.start_date.isoformat() if ab_test.start_date else None,
            "end_date": ab_test.end_date.isoformat() if ab_test.end_date else None,
            "winner_variant": ab_test.winner_variant,
            "winner_selected_at": ab_test.winner_selected_at.isoformat() if ab_test.winner_selected_at else None,
            "variants": variant_results
        }
    
    async def select_random_variant(self, test_id: str) -> Optional[DBEmailABVariant]:
        """
        Select random variant for sending (weighted distribution).
        
        Args:
            test_id: A/B test ID
            
        Returns:
            Randomly selected variant based on weights
        """
        variants = await self.get_variants_by_test(test_id)
        
        if not variants:
            return None
        
        # Weighted random selection
        weights = [v.weight for v in variants]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(variants)
        
        # Normalize weights
        normalized_weights = [w / total_weight for w in weights]
        
        # Random selection
        selected = random.choices(variants, weights=normalized_weights, k=1)[0]
        return selected

