"""
Tests for ClientRepository
Tests database operations for client entity
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.client_repository import ClientRepository
from core.exceptions import DuplicateEntityException
from tests.factories import ClientFactory


@pytest.mark.integration
class TestClientRepositorySave:
    """Test saving clients"""
    
    @pytest.mark.asyncio
    async def test_save_new_client(self, db_session: AsyncSession):
        """Test saving a new client"""
        repository = ClientRepository(db_session)
        client = ClientFactory.build()
        
        saved_client = await repository.save(client)
        await db_session.commit()
        
        assert saved_client.id is not None
        assert saved_client.name == client.name
        assert saved_client.subdomain == client.subdomain
    
    @pytest.mark.asyncio
    async def test_save_client_with_duplicate_subdomain_raises_exception(self, db_session: AsyncSession):
        """Test saving client with duplicate subdomain raises exception"""
        repository = ClientRepository(db_session)
        
        # Create first client
        client1 = ClientFactory.build(subdomain="duplicate-subdomain")
        await repository.save(client1)
        await db_session.commit()
        
        # Try to create second client with same subdomain
        client2 = ClientFactory.build(subdomain="duplicate-subdomain")
        
        with pytest.raises(DuplicateEntityException):
            await repository.save(client2)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_save_updates_existing_client(self, db_session: AsyncSession):
        """Test saving existing client updates it"""
        repository = ClientRepository(db_session)
        
        # Create client
        client = ClientFactory.build(name="Original Name")
        saved_client = await repository.save(client)
        await db_session.commit()
        
        # Update client
        saved_client.name = "Updated Name"
        updated_client = await repository.save(saved_client)
        await db_session.commit()
        
        assert updated_client.id == saved_client.id
        assert updated_client.name == "Updated Name"


@pytest.mark.integration
class TestClientRepositoryFind:
    """Test finding clients"""
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_client(self, db_session: AsyncSession):
        """Test find_by_id returns existing client"""
        repository = ClientRepository(db_session)
        
        # Create client
        client = ClientFactory.build()
        saved_client = await repository.save(client)
        await db_session.commit()
        
        # Find client
        found_client = await repository.find_by_id(saved_client.id)
        
        assert found_client is not None
        assert found_client.id == saved_client.id
        assert found_client.subdomain == saved_client.subdomain
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test find_by_id returns None for nonexistent client"""
        repository = ClientRepository(db_session)
        
        found_client = await repository.find_by_id("nonexistent-id")
        
        assert found_client is None
    
    @pytest.mark.asyncio
    async def test_find_by_subdomain_returns_client(self, db_session: AsyncSession):
        """Test find_by_subdomain returns existing client"""
        repository = ClientRepository(db_session)
        
        # Create client
        client = ClientFactory.build(subdomain="test-subdomain")
        await repository.save(client)
        await db_session.commit()
        
        # Find client
        found_client = await repository.find_by_subdomain("test-subdomain")
        
        assert found_client is not None
        assert found_client.subdomain == "test-subdomain"
    
    @pytest.mark.asyncio
    async def test_find_by_subdomain_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test find_by_subdomain returns None for nonexistent subdomain"""
        repository = ClientRepository(db_session)
        
        found_client = await repository.find_by_subdomain("nonexistent-subdomain")
        
        assert found_client is None
    
    @pytest.mark.asyncio
    async def test_find_by_api_key_returns_client(self, db_session: AsyncSession):
        """Test find_by_api_key returns existing client"""
        repository = ClientRepository(db_session)
        
        # Create client
        client = ClientFactory.build()
        api_key = client.api_key
        await repository.save(client)
        await db_session.commit()
        
        # Find client by API key
        found_client = await repository.find_by_api_key(api_key)
        
        assert found_client is not None
        assert found_client.id == client.id
    
    @pytest.mark.asyncio
    async def test_find_by_api_key_returns_none_for_invalid_key(self, db_session: AsyncSession):
        """Test find_by_api_key returns None for invalid API key"""
        repository = ClientRepository(db_session)
        
        found_client = await repository.find_by_api_key("invalid-api-key")
        
        assert found_client is None


@pytest.mark.integration
class TestClientRepositoryFindAll:
    """Test finding all clients"""
    
    @pytest.mark.asyncio
    async def test_find_all_returns_all_clients(self, db_session: AsyncSession):
        """Test find_all returns all clients"""
        repository = ClientRepository(db_session)
        
        # Get initial count
        initial_clients = await repository.find_all()
        initial_count = len(initial_clients)
        
        # Create multiple clients
        for i in range(3):
            client = ClientFactory.build()
            await repository.save(client)
        await db_session.commit()
        
        # Find all
        clients = await repository.find_all()
        
        assert len(clients) >= initial_count + 3
    
    @pytest.mark.asyncio
    async def test_find_all_returns_only_active_when_filtered(self, db_session: AsyncSession):
        """Test find_all can filter by active status"""
        repository = ClientRepository(db_session)
        
        # Create active and inactive clients
        active_client = ClientFactory.build(active=True)
        inactive_client = ClientFactory.build(active=False)
        await repository.save(active_client)
        await repository.save(inactive_client)
        await db_session.commit()
        
        # Get all clients
        all_clients = await repository.find_all()
        
        # Should include both active and inactive
        assert len(all_clients) >= 2


@pytest.mark.integration
class TestClientRepositoryDelete:
    """Test deleting clients"""
    
    @pytest.mark.asyncio
    async def test_delete_existing_client(self, db_session: AsyncSession):
        """Test deleting existing client"""
        repository = ClientRepository(db_session)
        
        # Create client
        client = ClientFactory.build()
        saved_client = await repository.save(client)
        await db_session.commit()
        
        # Delete client
        result = await repository.delete(saved_client.id)
        await db_session.commit()
        
        assert result is True
        
        # Verify client is deleted
        found_client = await repository.find_by_id(saved_client.id)
        assert found_client is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_client_returns_false(self, db_session: AsyncSession):
        """Test deleting nonexistent client returns False"""
        repository = ClientRepository(db_session)
        
        result = await repository.delete("nonexistent-id")
        
        assert result is False


@pytest.mark.integration
class TestClientRepositoryUniqueness:
    """Test uniqueness constraints"""
    
    @pytest.mark.asyncio
    async def test_subdomain_must_be_unique(self, db_session: AsyncSession):
        """Test subdomain uniqueness is enforced"""
        repository = ClientRepository(db_session)
        
        # Create first client
        client1 = ClientFactory.build(subdomain="unique-test")
        await repository.save(client1)
        await db_session.commit()
        
        # Try to create second client with same subdomain
        client2 = ClientFactory.build(subdomain="unique-test")
        
        with pytest.raises(DuplicateEntityException):
            await repository.save(client2)
            await db_session.commit()

