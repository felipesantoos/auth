"""
Unit tests for Email A/B Test Repository
Tests email A/B testing data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestEmailABTestRepository:
    """Test email A/B test repository"""
    
    @pytest.mark.asyncio
    async def test_save_ab_test(self):
        """Test saving A/B test"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.email_ab_test_repository import EmailABTestRepository
        repository = EmailABTestRepository(session_mock)
        
        test_data = Mock(
            id=None,
            name="Welcome Email Test",
            template_a="welcome_v1",
            template_b="welcome_v2",
            split_percentage=50
        )
        
        await repository.save(test_data)
        
        session_mock.add.assert_called_once()
        # Commit is not automatic in repositories
    
    @pytest.mark.asyncio
    async def test_get_active_tests(self):
        """Test getting active A/B tests"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        from infra.database.repositories.email_ab_test_repository import EmailABTestRepository
        repository = EmailABTestRepository(session_mock)
        
        result = await repository.get_active_tests()
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_test_results(self):
        """Test getting A/B test results"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        
        from infra.database.repositories.email_ab_test_repository import EmailABTestRepository
        repository = EmailABTestRepository(session_mock)
        
        result = await repository.get_test_results("test-123")
        
        session_mock.execute.assert_called()

