"""
Audit Repository Factory
Provides appropriate repository based on configuration (PostgreSQL vs Elasticsearch)
"""
import logging
from typing import Union

from config.settings import settings
from infra.database.repositories.audit_log_repository import AuditLogRepository
from core.interfaces.secondary.audit_log_repository_interface import IAuditLogRepository

logger = logging.getLogger(__name__)


class AuditRepositoryFactory:
    """
    Factory for creating audit repositories.
    
    Returns appropriate repository based on:
    - Configuration (ELASTICSEARCH_ENABLED)
    - Data volume
    - Performance requirements
    
    Strategies:
    - < 10M logs: PostgreSQL only (fast enough)
    - 10-100M logs: PostgreSQL + Elasticsearch (hybrid)
    - > 100M logs: Partitioned PostgreSQL + Elasticsearch
    
    Usage:
        repository = AuditRepositoryFactory.create_repository(session)
        await repository.save(audit_log)
    """
    
    @staticmethod
    def create_repository(
        session = None,  # AsyncSession for PostgreSQL
        force_elasticsearch: bool = False
    ) -> IAuditLogRepository:
        """
        Create appropriate audit repository.
        
        Args:
            session: SQLAlchemy AsyncSession (required for PostgreSQL)
            force_elasticsearch: Force Elasticsearch even if disabled in settings
            
        Returns:
            Audit repository instance (PostgreSQL or Elasticsearch)
        """
        # Check if Elasticsearch is enabled
        use_elasticsearch = settings.elasticsearch_enabled or force_elasticsearch
        
        if use_elasticsearch:
            try:
                # Try to create Elasticsearch repository
                es_repository = AuditRepositoryFactory._create_elasticsearch_repository()
                
                if es_repository:
                    logger.info("Using Elasticsearch for audit logs")
                    return es_repository
                else:
                    logger.warning("Elasticsearch enabled but unavailable, falling back to PostgreSQL")
            
            except Exception as e:
                logger.warning(f"Failed to create Elasticsearch repository: {e}, using PostgreSQL")
        
        # Fall back to PostgreSQL
        if not session:
            raise ValueError("PostgreSQL session required for AuditLogRepository")
        
        logger.info("Using PostgreSQL for audit logs")
        return AuditLogRepository(session)
    
    @staticmethod
    def _create_elasticsearch_repository():
        """
        Create Elasticsearch repository (if available).
        
        Returns:
            ElasticsearchAuditRepository or None
        """
        try:
            from infra.elasticsearch.elasticsearch_audit_repository import ElasticsearchAuditRepository
            from elasticsearch import AsyncElasticsearch
            
            # Create Elasticsearch client
            es_client = AsyncElasticsearch(
                hosts=[f"{settings.elasticsearch_host}:{settings.elasticsearch_port}"],
                # Add authentication if configured
                basic_auth=(
                    (settings.elasticsearch_user, settings.elasticsearch_password)
                    if settings.elasticsearch_user
                    else None
                )
            )
            
            # Create repository
            repository = ElasticsearchAuditRepository(
                elasticsearch_client=es_client,
                index_prefix=settings.elasticsearch_index_prefix
            )
            
            return repository
            
        except ImportError as e:
            logger.warning(f"Elasticsearch package not installed: {e}")
            logger.info("Install with: pip install 'elasticsearch[async]>=8.10.0'")
            return None
        except Exception as e:
            logger.error(f"Error creating Elasticsearch repository: {e}")
            return None
    
    @staticmethod
    def create_hybrid_repository(session):
        """
        Create hybrid repository (PostgreSQL + Elasticsearch).
        
        Dual-write strategy:
        - Write to PostgreSQL (source of truth)
        - Async write to Elasticsearch (search & analytics)
        
        Args:
            session: SQLAlchemy AsyncSession
            
        Returns:
            HybridAuditRepository (writes to both)
        """
        # TODO: Implement HybridAuditRepository for dual-write
        # For now, return PostgreSQL only
        logger.info("Hybrid repository not yet implemented, using PostgreSQL")
        return AuditLogRepository(session)
    
    @staticmethod
    def get_recommendation(estimated_logs: int) -> str:
        """
        Get repository recommendation based on data volume.
        
        Args:
            estimated_logs: Estimated number of audit logs
            
        Returns:
            Recommendation string
        """
        if estimated_logs < 1_000_000:
            return "postgresql_only"
        elif estimated_logs < 10_000_000:
            return "postgresql_with_indexes"
        elif estimated_logs < 100_000_000:
            return "postgresql_elasticsearch_hybrid"
        else:
            return "partitioned_postgresql_elasticsearch"

