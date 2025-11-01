"""
Email A/B Test Service
Business logic for email A/B testing operations
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime

from core.interfaces.primary.email_ab_test_service_interface import IEmailABTestService
from core.interfaces.secondary.email_service_interface import IEmailService
from infra.database.repositories.email_ab_test_repository import EmailABTestRepository

logger = logging.getLogger(__name__)


class EmailABTestService(IEmailABTestService):
    """
    Service for email A/B testing operations.
    
    Features:
    - Create and manage A/B tests
    - Distribute emails across variants
    - Track variant performance
    - Calculate statistical winners
    - Auto-select winning variants
    """
    
    def __init__(
        self,
        ab_test_repository: EmailABTestRepository,
        email_service: IEmailService
    ):
        """
        Initialize A/B test service.
        
        Args:
            ab_test_repository: Repository for A/B tests
            email_service: Email service for sending
        """
        self.ab_test_repo = ab_test_repository
        self.email_service = email_service
    
    async def create_test(
        self,
        name: str,
        description: Optional[str] = None,
        variant_count: int = 2,
        min_sample_size: int = 100,
        confidence_level: int = 95
    ) -> Dict:
        """Create new A/B test."""
        try:
            test = await self.ab_test_repo.create({
                "name": name,
                "description": description,
                "variant_count": variant_count,
                "min_sample_size": min_sample_size,
                "confidence_level": confidence_level,
                "status": "draft"
            })
            
            logger.info(f"A/B test created: {test.id} - {name}")
            
            return {
                "test_id": test.id,
                "name": test.name,
                "status": test.status,
                "variant_count": test.variant_count
            }
        
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}", exc_info=True)
            raise
    
    async def add_variant(
        self,
        test_id: str,
        variant_name: str,
        template_name: str,
        subject_template: str,
        weight: float = 1.0,
        context: Optional[dict] = None
    ) -> Dict:
        """Add variant to A/B test."""
        try:
            variant = await self.ab_test_repo.create_variant({
                "ab_test_id": test_id,
                "variant_name": variant_name,
                "template_name": template_name,
                "subject_template": subject_template,
                "weight": weight,
                "context": context or {}
            })
            
            logger.info(f"Variant {variant_name} added to test {test_id}")
            
            return {
                "variant_id": variant.id,
                "variant_name": variant.variant_name,
                "template": variant.template_name,
                "weight": variant.weight
            }
        
        except Exception as e:
            logger.error(f"Error adding variant: {e}", exc_info=True)
            raise
    
    async def start_test(self, test_id: str) -> bool:
        """Start A/B test."""
        try:
            test = await self.ab_test_repo.get_by_id(test_id)
            if not test:
                return False
            
            # Verify has at least 2 variants
            variants = await self.ab_test_repo.get_variants_by_test(test_id)
            if len(variants) < 2:
                raise ValueError("A/B test must have at least 2 variants")
            
            test.status = "active"
            test.start_date = datetime.utcnow()
            await self.ab_test_repo.update(test)
            
            logger.info(f"A/B test started: {test_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting test: {e}", exc_info=True)
            raise
    
    async def send_ab_test_email(
        self,
        test_id: str,
        recipients: List[str],
        base_context: Optional[dict] = None
    ) -> List[Dict]:
        """Send emails using A/B test variant distribution."""
        try:
            results = []
            
            for recipient in recipients:
                # Select random variant
                variant = await self.ab_test_repo.select_random_variant(test_id)
                
                if not variant:
                    logger.warning(f"No variant found for test {test_id}")
                    continue
                
                # Merge contexts
                context = {**(base_context or {}), **(variant.context or {})}
                
                # Format subject with context
                subject = variant.subject_template.format(**context)
                
                # Send email using variant's template
                result = await self.email_service.send_template_email(
                    to=[recipient],
                    subject=subject,
                    template_name=variant.template_name,
                    context=context,
                    tags=[f"ab_test:{test_id}", f"variant:{variant.variant_name}"]
                )
                
                # Update variant metrics
                await self.ab_test_repo.increment_variant_metrics(
                    variant_id=variant.id,
                    sent=1
                )
                
                results.append({
                    "email": recipient,
                    "variant": variant.variant_name,
                    **result
                })
            
            logger.info(f"A/B test emails sent: {len(results)} emails for test {test_id}")
            return results
        
        except Exception as e:
            logger.error(f"Error sending A/B test emails: {e}", exc_info=True)
            raise
    
    async def get_test_results(self, test_id: str) -> Dict:
        """Get A/B test results and statistics."""
        try:
            return await self.ab_test_repo.get_test_results(test_id)
        
        except Exception as e:
            logger.error(f"Error getting test results: {e}", exc_info=True)
            raise
    
    async def calculate_winner(
        self,
        test_id: str,
        metric: str = "open_rate"
    ) -> Optional[Dict]:
        """Calculate winner based on metric."""
        try:
            winner = await self.ab_test_repo.calculate_winner(test_id, metric)
            
            if not winner:
                return None
            
            return {
                "variant_id": winner.id,
                "variant_name": winner.variant_name,
                "template": winner.template_name,
                "metric": metric,
                "value": getattr(winner, metric, 0) if hasattr(winner, metric) else 0
            }
        
        except Exception as e:
            logger.error(f"Error calculating winner: {e}", exc_info=True)
            raise
    
    async def declare_winner(
        self,
        test_id: str,
        variant_name: str
    ) -> bool:
        """Manually declare winner."""
        try:
            test = await self.ab_test_repo.get_by_id(test_id)
            if not test:
                return False
            
            # Mark winner in test
            test.winner_variant = variant_name
            test.winner_selected_at = datetime.utcnow()
            test.status = "completed"
            await self.ab_test_repo.update(test)
            
            # Mark variant as winner
            variants = await self.ab_test_repo.get_variants_by_test(test_id)
            for variant in variants:
                variant.is_winner = (variant.variant_name == variant_name)
                await self.ab_test_repo.update_variant(variant)
            
            logger.info(f"Winner declared for test {test_id}: Variant {variant_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error declaring winner: {e}", exc_info=True)
            raise
    
    async def stop_test(self, test_id: str) -> bool:
        """Stop A/B test."""
        try:
            test = await self.ab_test_repo.get_by_id(test_id)
            if not test:
                return False
            
            test.status = "paused"
            test.end_date = datetime.utcnow()
            await self.ab_test_repo.update(test)
            
            logger.info(f"A/B test stopped: {test_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping test: {e}", exc_info=True)
            raise

