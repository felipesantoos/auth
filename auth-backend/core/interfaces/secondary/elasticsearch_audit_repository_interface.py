"""
Elasticsearch Audit Repository Interface
For fast search and analytics on millions of audit logs
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.domain.auth.audit_log import AuditLog
from core.domain.audit.audit_event_category import AuditEventCategory


class IElasticsearchAuditRepository(ABC):
    """
    Interface for Elasticsearch-based audit log repository.
    
    Purpose:
    - Fast full-text search across millions of logs
    - Real-time analytics and aggregations
    - Scalable to 100M+ audit logs
    
    When to use:
    - PostgreSQL queries become slow (>10M logs)
    - Need real-time dashboards
    - Complex search requirements
    - Analytics and reporting
    
    Implementation:
    - Primary storage: PostgreSQL (source of truth)
    - Secondary index: Elasticsearch (search & analytics)
    - Dual-write or async sync pattern
    """
    
    @abstractmethod
    async def index_audit_log(self, audit_log: AuditLog) -> bool:
        """
        Index single audit log in Elasticsearch.
        
        Args:
            audit_log: Audit log to index
            
        Returns:
            True if successfully indexed
        """
        pass
    
    @abstractmethod
    async def index_batch(self, audit_logs: List[AuditLog]) -> Dict[str, Any]:
        """
        Index multiple audit logs in batch (for performance).
        
        Args:
            audit_logs: List of audit logs to index
            
        Returns:
            Result dict with success/failure counts
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        size: int = 100,
        from_: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fast full-text search in audit logs.
        
        Searches across: action, description, resource_name, username
        
        Args:
            query: Search query (full-text)
            filters: Optional filters (user_id, event_category, tags, etc.)
            size: Max results to return
            from_: Offset for pagination
            
        Returns:
            List of matching audit logs (as dicts)
        """
        pass
    
    @abstractmethod
    async def aggregate_by_category(
        self,
        start_date: datetime,
        end_date: datetime,
        client_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Aggregate events by category (for analytics).
        
        Args:
            start_date: Start date
            end_date: End date
            client_id: Optional client filter
            
        Returns:
            Dict of {category: count}
        """
        pass
    
    @abstractmethod
    async def get_user_timeline(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user activity timeline using Elasticsearch aggregations.
        
        Much faster than PostgreSQL for large datasets.
        
        Args:
            user_id: User ID
            days: Number of days
            
        Returns:
            List of {date, count}
        """
        pass
    
    @abstractmethod
    async def get_top_users(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
        client_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most active users (for analytics).
        
        Args:
            start_date: Start date
            end_date: End date
            limit: Max users to return
            client_id: Optional client filter
            
        Returns:
            List of {username, count}
        """
        pass
    
    @abstractmethod
    async def delete_by_query(
        self,
        filters: Dict[str, Any]
    ) -> int:
        """
        Delete audit logs matching filters (for cleanup).
        
        Args:
            filters: Filters to apply
            
        Returns:
            Number of documents deleted
        """
        pass
    
    @abstractmethod
    async def reindex_from_postgresql(
        self,
        start_date: Optional[datetime] = None,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Reindex audit logs from PostgreSQL to Elasticsearch.
        
        Used for:
        - Initial migration to Elasticsearch
        - Recovery after Elasticsearch failure
        - Backfill historical data
        
        Args:
            start_date: Optional start date (None = all logs)
            batch_size: Batch size for processing
            
        Returns:
            Result dict with indexed count
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Elasticsearch connection health.
        
        Returns:
            Health status dict
        """
        pass

