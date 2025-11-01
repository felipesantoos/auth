"""
Email A/B Test Service Interface
Primary port for email A/B testing operations
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime


class IEmailABTestService(ABC):
    """Interface for email A/B testing service operations."""
    
    @abstractmethod
    async def create_test(
        self,
        name: str,
        description: Optional[str] = None,
        variant_count: int = 2,
        min_sample_size: int = 100,
        confidence_level: int = 95
    ) -> Dict:
        """
        Create new A/B test.
        
        Args:
            name: Test name
            description: Test description
            variant_count: Number of variants (2=A/B, 3=A/B/C)
            min_sample_size: Minimum emails per variant
            confidence_level: Statistical confidence level (95, 99)
            
        Returns:
            Created test data
        """
        pass
    
    @abstractmethod
    async def add_variant(
        self,
        test_id: str,
        variant_name: str,
        template_name: str,
        subject_template: str,
        weight: float = 1.0,
        context: Optional[dict] = None
    ) -> Dict:
        """
        Add variant to A/B test.
        
        Args:
            test_id: A/B test ID
            variant_name: Variant identifier ('A', 'B', 'C')
            template_name: Email template to use
            subject_template: Subject line template
            weight: Distribution weight (0.5 = 50%)
            context: Template variables
            
        Returns:
            Created variant data
        """
        pass
    
    @abstractmethod
    async def start_test(self, test_id: str) -> bool:
        """
        Start A/B test.
        
        Args:
            test_id: A/B test ID
            
        Returns:
            True if started successfully
        """
        pass
    
    @abstractmethod
    async def send_ab_test_email(
        self,
        test_id: str,
        recipients: List[str],
        base_context: Optional[dict] = None
    ) -> List[Dict]:
        """
        Send emails using A/B test variant distribution.
        
        Args:
            test_id: A/B test ID
            recipients: List of email addresses
            base_context: Shared context for all variants
            
        Returns:
            List of send results
        """
        pass
    
    @abstractmethod
    async def get_test_results(self, test_id: str) -> Dict:
        """
        Get A/B test results and statistics.
        
        Args:
            test_id: A/B test ID
            
        Returns:
            Test results with variant metrics
        """
        pass
    
    @abstractmethod
    async def calculate_winner(
        self,
        test_id: str,
        metric: str = "open_rate"
    ) -> Optional[Dict]:
        """
        Calculate winner based on metric.
        
        Args:
            test_id: A/B test ID
            metric: Metric to compare ('open_rate', 'click_rate', 'ctr')
            
        Returns:
            Winner variant data or None if inconclusive
        """
        pass
    
    @abstractmethod
    async def declare_winner(
        self,
        test_id: str,
        variant_name: str
    ) -> bool:
        """
        Manually declare winner.
        
        Args:
            test_id: A/B test ID
            variant_name: Winning variant name
            
        Returns:
            True if declared successfully
        """
        pass
    
    @abstractmethod
    async def stop_test(self, test_id: str) -> bool:
        """
        Stop A/B test.
        
        Args:
            test_id: A/B test ID
            
        Returns:
            True if stopped successfully
        """
        pass

