"""
Elasticsearch Audit Repository Implementation
Fast search and analytics for millions of audit logs
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from core.domain.auth.audit_log import AuditLog
from core.domain.audit.audit_event_category import AuditEventCategory
from core.interfaces.secondary.elasticsearch_audit_repository_interface import IElasticsearchAuditRepository

logger = logging.getLogger(__name__)


class ElasticsearchAuditRepository(IElasticsearchAuditRepository):
    """
    Elasticsearch repository for fast audit log search and analytics.
    
    Features:
    - Full-text search across all fields
    - Real-time aggregations and analytics
    - Scales to 100M+ logs
    - Sub-second query response times
    
    Usage:
        # In settings: ELASTICSEARCH_ENABLED=true
        repository = ElasticsearchAuditRepository(es_client)
        await repository.index_audit_log(audit_log)
        results = await repository.search("password changed", filters={"user_id": "123"})
    
    Note:
        Requires elasticsearch[async] package:
        pip install 'elasticsearch[async]>=8.10.0'
    """
    
    def __init__(self, elasticsearch_client=None, index_prefix: str = "audit_logs"):
        """
        Initialize Elasticsearch repository.
        
        Args:
            elasticsearch_client: AsyncElasticsearch client (optional, lazy loaded)
            index_prefix: Index name prefix
        """
        self.es_client = elasticsearch_client
        self.index_name = f"{index_prefix}"
        self.is_enabled = False
    
    async def _get_client(self):
        """
        Get Elasticsearch client (lazy initialization).
        
        Returns None if Elasticsearch is not enabled/configured.
        """
        if self.es_client:
            return self.es_client
        
        try:
            # Try to import and create client
            from elasticsearch import AsyncElasticsearch
            from config.settings import settings
            
            if not settings.elasticsearch_enabled:
                logger.debug("Elasticsearch is disabled")
                return None
            
            self.es_client = AsyncElasticsearch(
                hosts=[f"{settings.elasticsearch_host}:{settings.elasticsearch_port}"],
                # Add authentication if needed
                # basic_auth=(settings.elasticsearch_user, settings.elasticsearch_password)
            )
            
            self.is_enabled = True
            return self.es_client
            
        except ImportError:
            logger.warning("elasticsearch package not installed. Install with: pip install 'elasticsearch[async]>=8.10.0'")
            return None
        except AttributeError:
            logger.warning("Elasticsearch settings not configured")
            return None
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch client: {e}")
            return None
    
    async def index_audit_log(self, audit_log: AuditLog) -> bool:
        """
        Index single audit log in Elasticsearch.
        
        Args:
            audit_log: Audit log to index
            
        Returns:
            True if successfully indexed
        """
        es = await self._get_client()
        if not es:
            return False
        
        try:
            # Convert audit log to Elasticsearch document
            doc = self._audit_log_to_document(audit_log)
            
            # Index document
            await es.index(
                index=self.index_name,
                id=audit_log.event_id,
                document=doc
            )
            
            logger.debug(f"Indexed audit log {audit_log.event_id} in Elasticsearch")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing audit log in Elasticsearch: {e}")
            return False
    
    async def index_batch(self, audit_logs: List[AuditLog]) -> Dict[str, Any]:
        """
        Index multiple audit logs in batch (bulk API).
        
        Args:
            audit_logs: List of audit logs
            
        Returns:
            Result dict with success/failure counts
        """
        es = await self._get_client()
        if not es:
            return {"success": 0, "failed": len(audit_logs), "error": "Elasticsearch not available"}
        
        try:
            from elasticsearch.helpers import async_bulk
            
            # Prepare bulk actions
            actions = []
            for audit_log in audit_logs:
                doc = self._audit_log_to_document(audit_log)
                actions.append({
                    "_index": self.index_name,
                    "_id": audit_log.event_id,
                    "_source": doc
                })
            
            # Bulk index
            success, failed = await async_bulk(es, actions, raise_on_error=False)
            
            logger.info(f"Bulk indexed {success} audit logs, {len(failed)} failed")
            
            return {
                "success": success,
                "failed": len(failed),
                "total": len(audit_logs)
            }
            
        except Exception as e:
            logger.error(f"Error in bulk indexing: {e}")
            return {"success": 0, "failed": len(audit_logs), "error": str(e)}
    
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        size: int = 100,
        from_: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fast full-text search in audit logs.
        
        Args:
            query: Search query
            filters: Optional filters
            size: Max results
            from_: Offset for pagination
            
        Returns:
            List of matching audit logs
        """
        es = await self._get_client()
        if not es:
            return []
        
        try:
            # Build Elasticsearch query
            must_clauses = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["action^2", "description", "resource_name", "username"],
                        "fuzziness": "AUTO"
                    }
                }
            ]
            
            # Add filters
            if filters:
                if "user_id" in filters:
                    must_clauses.append({"term": {"user_id": filters["user_id"]}})
                
                if "client_id" in filters:
                    must_clauses.append({"term": {"client_id": filters["client_id"]}})
                
                if "event_category" in filters:
                    must_clauses.append({"term": {"event_category": filters["event_category"]}})
                
                if "resource_type" in filters:
                    must_clauses.append({"term": {"resource_type": filters["resource_type"]}})
                
                if "success" in filters:
                    must_clauses.append({"term": {"success": filters["success"]}})
                
                if "tags" in filters:
                    must_clauses.append({"terms": {"tags": filters["tags"]}})
                
                if "start_date" in filters:
                    must_clauses.append({
                        "range": {
                            "created_at": {
                                "gte": filters["start_date"].isoformat()
                            }
                        }
                    })
            
            # Build search body
            search_body = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                },
                "sort": [
                    {"created_at": {"order": "desc"}}
                ],
                "size": size,
                "from": from_
            }
            
            # Execute search
            result = await es.search(
                index=self.index_name,
                body=search_body
            )
            
            # Extract hits
            return [hit["_source"] for hit in result["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Error searching Elasticsearch: {e}")
            return []
    
    async def aggregate_by_category(
        self,
        start_date: datetime,
        end_date: datetime,
        client_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Aggregate events by category using Elasticsearch aggregations.
        
        Args:
            start_date: Start date
            end_date: End date
            client_id: Optional client filter
            
        Returns:
            Dict of {category: count}
        """
        es = await self._get_client()
        if not es:
            return {}
        
        try:
            # Build query
            must_clauses = [
                {
                    "range": {
                        "created_at": {
                            "gte": start_date.isoformat(),
                            "lte": end_date.isoformat()
                        }
                    }
                }
            ]
            
            if client_id:
                must_clauses.append({"term": {"client_id": client_id}})
            
            # Aggregation query
            agg_body = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                },
                "size": 0,  # Don't return documents
                "aggs": {
                    "by_category": {
                        "terms": {
                            "field": "event_category",
                            "size": 10
                        }
                    }
                }
            }
            
            result = await es.search(
                index=self.index_name,
                body=agg_body
            )
            
            # Extract aggregation results
            buckets = result["aggregations"]["by_category"]["buckets"]
            return {bucket["key"]: bucket["doc_count"] for bucket in buckets}
            
        except Exception as e:
            logger.error(f"Error in Elasticsearch aggregation: {e}")
            return {}
    
    async def get_user_timeline(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user activity timeline using date histogram aggregation.
        
        Args:
            user_id: User ID
            days: Number of days
            
        Returns:
            List of {date, count}
        """
        es = await self._get_client()
        if not es:
            return []
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            agg_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"user_id": user_id}},
                            {"range": {"created_at": {"gte": start_date.isoformat()}}}
                        ]
                    }
                },
                "size": 0,
                "aggs": {
                    "timeline": {
                        "date_histogram": {
                            "field": "created_at",
                            "calendar_interval": "day",
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
            
            result = await es.search(
                index=self.index_name,
                body=agg_body
            )
            
            buckets = result["aggregations"]["timeline"]["buckets"]
            return [
                {"date": bucket["key_as_string"], "count": bucket["doc_count"]}
                for bucket in buckets
            ]
            
        except Exception as e:
            logger.error(f"Error getting user timeline from Elasticsearch: {e}")
            return []
    
    async def get_top_users(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
        client_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most active users.
        
        Args:
            start_date: Start date
            end_date: End date
            limit: Max users
            client_id: Optional client filter
            
        Returns:
            List of {username, count}
        """
        es = await self._get_client()
        if not es:
            return []
        
        try:
            must_clauses = [
                {
                    "range": {
                        "created_at": {
                            "gte": start_date.isoformat(),
                            "lte": end_date.isoformat()
                        }
                    }
                }
            ]
            
            if client_id:
                must_clauses.append({"term": {"client_id": client_id}})
            
            agg_body = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                },
                "size": 0,
                "aggs": {
                    "top_users": {
                        "terms": {
                            "field": "username",
                            "size": limit,
                            "order": {"_count": "desc"}
                        }
                    }
                }
            }
            
            result = await es.search(
                index=self.index_name,
                body=agg_body
            )
            
            buckets = result["aggregations"]["top_users"]["buckets"]
            return [
                {"username": bucket["key"], "count": bucket["doc_count"]}
                for bucket in buckets
            ]
            
        except Exception as e:
            logger.error(f"Error getting top users from Elasticsearch: {e}")
            return []
    
    async def delete_by_query(self, filters: Dict[str, Any]) -> int:
        """
        Delete audit logs matching filters.
        
        Args:
            filters: Filters to apply
            
        Returns:
            Number of documents deleted
        """
        es = await self._get_client()
        if not es:
            return 0
        
        try:
            # Build delete query
            must_clauses = []
            
            for key, value in filters.items():
                must_clauses.append({"term": {key: value}})
            
            delete_body = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                }
            }
            
            result = await es.delete_by_query(
                index=self.index_name,
                body=delete_body
            )
            
            deleted = result.get("deleted", 0)
            logger.info(f"Deleted {deleted} documents from Elasticsearch")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting from Elasticsearch: {e}")
            return 0
    
    async def reindex_from_postgresql(
        self,
        start_date: Optional[datetime] = None,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Reindex audit logs from PostgreSQL to Elasticsearch.
        
        Used for initial migration or recovery.
        
        Args:
            start_date: Optional start date (None = all logs)
            batch_size: Batch size for processing
            
        Returns:
            Result dict with counts
        """
        es = await self._get_client()
        if not es:
            return {"error": "Elasticsearch not available"}
        
        try:
            # This would need PostgreSQL repository injected
            # For now, return placeholder
            logger.info("Reindex from PostgreSQL requested")
            
            return {
                "status": "not_implemented",
                "message": "Inject PostgreSQL repository to enable reindexing"
            }
            
        except Exception as e:
            logger.error(f"Error reindexing: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Elasticsearch connection health.
        
        Returns:
            Health status dict
        """
        es = await self._get_client()
        if not es:
            return {
                "status": "unavailable",
                "elasticsearch_enabled": False
            }
        
        try:
            # Ping Elasticsearch
            is_alive = await es.ping()
            
            if is_alive:
                # Get cluster health
                health = await es.cluster.health()
                
                return {
                    "status": "healthy",
                    "elasticsearch_enabled": True,
                    "cluster_name": health.get("cluster_name"),
                    "cluster_status": health.get("status"),
                    "number_of_nodes": health.get("number_of_nodes")
                }
            else:
                return {
                    "status": "unreachable",
                    "elasticsearch_enabled": True
                }
                
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return {
                "status": "error",
                "elasticsearch_enabled": True,
                "error": str(e)
            }
    
    # ===== Helper Methods =====
    
    def _audit_log_to_document(self, audit_log: AuditLog) -> Dict[str, Any]:
        """
        Convert AuditLog domain model to Elasticsearch document.
        
        Args:
            audit_log: Audit log domain object
            
        Returns:
            Elasticsearch document (dict)
        """
        doc = {
            "event_id": audit_log.event_id,
            "event_type": audit_log.event_type.value if audit_log.event_type else None,
            "event_category": audit_log.event_category.value if audit_log.event_category else None,
            "action": audit_log.action,
            "description": audit_log.description,
            
            # Actor
            "user_id": audit_log.user_id,
            "username": audit_log.username,
            "user_email": audit_log.user_email,
            "impersonated_by": audit_log.impersonated_by,
            
            # Tenant
            "client_id": audit_log.client_id,
            
            # Resource
            "resource_type": audit_log.resource_type,
            "resource_id": audit_log.resource_id,
            "resource_name": audit_log.resource_name,
            
            # Context
            "ip_address": audit_log.ip_address,
            "user_agent": audit_log.user_agent,
            "location": audit_log.location,
            "request_id": audit_log.request_id,
            "session_id": audit_log.session_id,
            
            # Changes
            "changes": audit_log.changes,
            "old_values": audit_log.old_values,
            "new_values": audit_log.new_values,
            
            # Metadata
            "metadata": audit_log.metadata,
            "tags": audit_log.tags,
            
            # Status
            "success": audit_log.success,
            "status": audit_log.status,
            "error_message": audit_log.error_message,
            
            # Timestamp
            "created_at": audit_log.created_at.isoformat() if audit_log.created_at else None
        }
        
        return doc
    
    async def create_index_mapping(self) -> bool:
        """
        Create index with optimized mapping for audit logs.
        
        Should be called once during setup.
        
        Returns:
            True if successful
        """
        es = await self._get_client()
        if not es:
            return False
        
        try:
            # Define index mapping
            mapping = {
                "mappings": {
                    "properties": {
                        "event_id": {"type": "keyword"},
                        "event_type": {"type": "keyword"},
                        "event_category": {"type": "keyword"},
                        "action": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "description": {"type": "text"},
                        
                        "user_id": {"type": "keyword"},
                        "username": {"type": "keyword"},
                        "user_email": {"type": "keyword"},
                        "client_id": {"type": "keyword"},
                        
                        "resource_type": {"type": "keyword"},
                        "resource_id": {"type": "keyword"},
                        "resource_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        
                        "ip_address": {"type": "ip"},
                        "location": {"type": "text"},
                        "request_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        
                        "changes": {"type": "object", "enabled": True},
                        "old_values": {"type": "object", "enabled": True},
                        "new_values": {"type": "object", "enabled": True},
                        "metadata": {"type": "object", "enabled": True},
                        
                        "tags": {"type": "keyword"},
                        "success": {"type": "boolean"},
                        "status": {"type": "keyword"},
                        "error_message": {"type": "text"},
                        
                        "created_at": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1,
                    "refresh_interval": "5s"
                }
            }
            
            # Create index
            await es.indices.create(
                index=self.index_name,
                body=mapping,
                ignore=400  # Ignore if already exists
            )
            
            logger.info(f"Created Elasticsearch index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Elasticsearch index: {e}")
            return False

