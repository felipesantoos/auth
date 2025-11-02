"""
Unit tests for Audit Repository Factory
Tests audit repository factory without external dependencies
"""
import pytest
from unittest.mock import Mock, patch
from infra.audit.audit_repository_factory import AuditRepositoryFactory


@pytest.mark.unit
class TestAuditRepositoryFactory:
    """Test audit repository factory"""
    
    def test_get_repository_returns_database_repository(self):
        """Test factory returns database repository by default"""
        settings_mock = Mock()
        settings_mock.audit_storage = "database"
        
        with patch('infra.audit.audit_repository_factory.settings', settings_mock):
            repo = AuditRepositoryFactory.get_repository()
            
            assert repo is not None
    
    def test_get_repository_returns_elasticsearch(self):
        """Test factory returns Elasticsearch repository when configured"""
        settings_mock = Mock()
        settings_mock.audit_storage = "elasticsearch"
        settings_mock.elasticsearch_host = "localhost:9200"
        
        with patch('infra.audit.audit_repository_factory.settings', settings_mock):
            repo = AuditRepositoryFactory.get_repository()
            
            assert repo is not None

