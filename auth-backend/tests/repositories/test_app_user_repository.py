"""
Tests for AppUserRepository
Tests database operations for user entity
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.app_user_repository import AppUserRepository
from core.services.filters.user_filter import UserFilter
from core.domain.auth.user_role import UserRole
from core.exceptions import DuplicateEntityException, EntityNotFoundException
from tests.factories import UserFactory


@pytest.mark.integration
class TestAppUserRepositorySave:
    """Test saving users"""
    
    @pytest.mark.asyncio
    async def test_save_new_user(self, db_session: AsyncSession):
        """Test saving a new user"""
        repository = AppUserRepository(db_session)
        user = UserFactory.create()
        
        saved_user = await repository.save(user)
        await db_session.commit()
        
        assert saved_user.id is not None
        assert saved_user.username == user.username
        assert saved_user.email == user.email
    
    @pytest.mark.asyncio
    async def test_save_user_with_duplicate_email_raises_exception(self, db_session: AsyncSession):
        """Test saving user with duplicate email raises exception"""
        repository = AppUserRepository(db_session)
        
        # Create first user
        user1 = UserFactory.create(email="duplicate@example.com")
        await repository.save(user1)
        await db_session.commit()
        
        # Try to create second user with same email
        user2 = UserFactory.create(email="duplicate@example.com")
        
        with pytest.raises(DuplicateEntityException):
            await repository.save(user2)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_save_updates_existing_user(self, db_session: AsyncSession):
        """Test saving existing user updates it"""
        repository = AppUserRepository(db_session)
        
        # Create user
        user = UserFactory.create(name="Original Name")
        saved_user = await repository.save(user)
        await db_session.commit()
        
        # Update user
        saved_user.name = "Updated Name"
        updated_user = await repository.save(saved_user)
        await db_session.commit()
        
        assert updated_user.id == saved_user.id
        assert updated_user.name == "Updated Name"


@pytest.mark.integration
class TestAppUserRepositoryFind:
    """Test finding users"""
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_user(self, db_session: AsyncSession):
        """Test find_by_id returns existing user"""
        repository = AppUserRepository(db_session)
        
        # Create user
        user = UserFactory.create()
        saved_user = await repository.save(user)
        await db_session.commit()
        
        # Find user
        found_user = await repository.find_by_id(saved_user.id, saved_user.client_id)
        
        assert found_user is not None
        assert found_user.id == saved_user.id
        assert found_user.email == saved_user.email
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test find_by_id returns None for nonexistent user"""
        repository = AppUserRepository(db_session)
        
        found_user = await repository.find_by_id("nonexistent-id", "client-123")
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_find_by_email_returns_user(self, db_session: AsyncSession):
        """Test find_by_email returns existing user"""
        repository = AppUserRepository(db_session)
        
        # Create user
        user = UserFactory.create(email="findme@example.com")
        await repository.save(user)
        await db_session.commit()
        
        # Find user
        found_user = await repository.find_by_email("findme@example.com", user.client_id)
        
        assert found_user is not None
        assert found_user.email == "findme@example.com"
    
    @pytest.mark.asyncio
    async def test_find_by_email_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test find_by_email returns None for nonexistent email"""
        repository = AppUserRepository(db_session)
        
        found_user = await repository.find_by_email("notfound@example.com", "client-123")
        
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_find_by_email_respects_client_isolation(self, db_session: AsyncSession):
        """Test find_by_email respects multi-tenant isolation"""
        repository = AppUserRepository(db_session)
        
        # Create user in client A
        user_a = UserFactory.create(
            email="user@example.com",
            client_id="client-a"
        )
        await repository.save(user_a)
        await db_session.commit()
        
        # Try to find in client B
        found_user = await repository.find_by_email("user@example.com", "client-b")
        
        # Should not find user from different client
        assert found_user is None


@pytest.mark.integration
class TestAppUserRepositoryFindAll:
    """Test finding all users with filters"""
    
    @pytest.mark.asyncio
    async def test_find_all_returns_all_users(self, db_session: AsyncSession):
        """Test find_all returns all users"""
        repository = AppUserRepository(db_session)
        
        # Create multiple users
        for i in range(3):
            user = UserFactory.create(client_id="client-123")
            await repository.save(user)
        await db_session.commit()
        
        # Find all
        filter = UserFilter(client_id="client-123")
        users = await repository.find_all(filter)
        
        assert len(users) >= 3
    
    @pytest.mark.asyncio
    async def test_find_all_with_role_filter(self, db_session: AsyncSession):
        """Test find_all with role filter"""
        repository = AppUserRepository(db_session)
        
        # Create users with different roles
        admin = UserFactory.create_admin(client_id="client-123")
        user = UserFactory.create(role=UserRole.USER, client_id="client-123")
        await repository.save(admin)
        await repository.save(user)
        await db_session.commit()
        
        # Find only admins
        filter = UserFilter(client_id="client-123", role=UserRole.ADMIN)
        users = await repository.find_all(filter)
        
        assert all(u.role == UserRole.ADMIN for u in users)
    
    @pytest.mark.asyncio
    async def test_find_all_with_active_filter(self, db_session: AsyncSession):
        """Test find_all with active filter"""
        repository = AppUserRepository(db_session)
        
        # Create active and inactive users
        active_user = UserFactory.create(active=True, client_id="client-123")
        inactive_user = UserFactory.create(active=False, client_id="client-123")
        await repository.save(active_user)
        await repository.save(inactive_user)
        await db_session.commit()
        
        # Find only active users
        filter = UserFilter(client_id="client-123", active=True)
        users = await repository.find_all(filter)
        
        assert all(u.active is True for u in users)
    
    @pytest.mark.asyncio
    async def test_find_all_respects_pagination(self, db_session: AsyncSession):
        """Test find_all respects pagination"""
        repository = AppUserRepository(db_session)
        
        # Create 5 users
        for i in range(5):
            user = UserFactory.create(client_id="client-123")
            await repository.save(user)
        await db_session.commit()
        
        # Get first page (2 items)
        filter = UserFilter(client_id="client-123", page=1, page_size=2)
        users_page1 = await repository.find_all(filter)
        
        # Get second page
        filter = UserFilter(client_id="client-123", page=2, page_size=2)
        users_page2 = await repository.find_all(filter)
        
        assert len(users_page1) == 2
        assert len(users_page2) == 2
        # Pages should have different users
        assert users_page1[0].id != users_page2[0].id


@pytest.mark.integration
class TestAppUserRepositoryDelete:
    """Test deleting users"""
    
    @pytest.mark.asyncio
    async def test_delete_existing_user(self, db_session: AsyncSession):
        """Test deleting existing user"""
        repository = AppUserRepository(db_session)
        
        # Create user
        user = UserFactory.create()
        saved_user = await repository.save(user)
        await db_session.commit()
        
        # Delete user
        result = await repository.delete(saved_user.id, saved_user.client_id)
        await db_session.commit()
        
        assert result is True
        
        # Verify user is deleted
        found_user = await repository.find_by_id(saved_user.id, saved_user.client_id)
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_returns_false(self, db_session: AsyncSession):
        """Test deleting nonexistent user returns False"""
        repository = AppUserRepository(db_session)
        
        result = await repository.delete("nonexistent-id", "client-123")
        
        assert result is False


@pytest.mark.integration
class TestAppUserRepositoryCount:
    """Test counting users"""
    
    @pytest.mark.asyncio
    async def test_count_returns_total_users(self, db_session: AsyncSession):
        """Test count returns total number of users"""
        repository = AppUserRepository(db_session)
        
        # Get initial count
        filter = UserFilter(client_id="client-test-count")
        initial_count = await repository.count(filter)
        
        # Create users
        for i in range(3):
            user = UserFactory.create(client_id="client-test-count")
            await repository.save(user)
        await db_session.commit()
        
        # Count again
        new_count = await repository.count(filter)
        
        assert new_count == initial_count + 3
    
    @pytest.mark.asyncio
    async def test_count_with_filters(self, db_session: AsyncSession):
        """Test count with filters"""
        repository = AppUserRepository(db_session)
        
        # Create active and inactive users
        active_user = UserFactory.create(active=True, client_id="client-count-filter")
        inactive_user = UserFactory.create(active=False, client_id="client-count-filter")
        await repository.save(active_user)
        await repository.save(inactive_user)
        await db_session.commit()
        
        # Count only active
        filter = UserFilter(client_id="client-count-filter", active=True)
        active_count = await repository.count(filter)
        
        # Count only inactive
        filter = UserFilter(client_id="client-count-filter", active=False)
        inactive_count = await repository.count(filter)
        
        assert active_count >= 1
        assert inactive_count >= 1

