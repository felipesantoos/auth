"""
Unit tests for Elasticsearch Audit Repository
Tests Elasticsearch audit storage without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.elasticsearch.elasticsearch_audit_repository import ElasticsearchAuditRepository


@pytest.mark.unit
class TestElasticsearchAuditRepository:
    """Test Elasticsearch audit repository"""
    
    @pytest.mark.asyncio
    async def test_save_audit_log_to_elasticsearch(self):
        """Test saving audit log to Elasticsearch"""
        es_client_mock = AsyncMock()
        es_client_mock.index = AsyncMock(return_value={"_id": "doc-123"})
        
        with patch('infra.elasticsearch.elasticsearch_audit_repository.get_es_client', return_value=es_client_mock):
            repository = ElasticsearchAuditRepository()
            
            audit_log = Mock(
                id="log-123",
                event_type=Mock(value="login_success"),
                client_id="client-123"
            )
            
            await repository.save(audit_log)
            
            es_client_mock.index.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_audit_logs(self):
        """Test searching audit logs in Elasticsearch"""
        es_client_mock = AsyncMock()
        es_client_mock.search = AsyncMock(return_value={
            "hits": {
                "hits": [
                    {"_source": {"event_type": "login_success", "user_id": "user-123"}}
                ]
            }
        })
        
        with patch('infra.elasticsearch.elasticsearch_audit_repository.get_es_client', return_value=es_client_mock):
            repository = ElasticsearchAuditRepository()
            
            results = await repository.search(query="login", filters={})
            
            es_client_mock.search.assert_called()
            assert isinstance(results, list)

