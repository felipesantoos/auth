"""
Performance tests for authentication system
Tests with large datasets (10K+ records)
"""
import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.filters.user_filter import UserFilter
from infra.database.repositories.app_user_repository import AppUserRepository
from infra.database.repositories.permission_repository import PermissionRepository
from tests.factories import UserFactory, PermissionFactory
from core.domain.auth.permission import PermissionAction


@pytest.mark.performance
@pytest.mark.slow
class TestUserListingPerformance:
    """Test user listing performance with large datasets"""
    
    @pytest.mark.asyncio
    async def test_pagination_with_10k_users(self, db_session: AsyncSession):
        """
        Test pagination performance with 10,000 users (as per guide spec).
        
        Should complete in < 2 seconds even with deep pagination.
        
        Note: This test creates 10K users, so it's VERY slow to setup (~5-10 min).
        Run explicitly with: pytest -m performance tests/performance/
        Skip in normal runs with: pytest -m "not performance"
        """
        repository = AppUserRepository(db_session)
        
        # Create 10,000 users (this will be slow, but only runs in performance tests)
        print("\n⏳ Creating 10,000 users for performance test (this will take ~5-10 minutes)...")
        users = await UserFactory.create_batch_persisted(db_session, count=10000, client_id="perf-test")
        print(f"✓ Created {len(users)} users for testing")
        
        # Test pagination performance at different depths
        print("\n📊 Testing pagination performance...")
        
        # Test deep pagination (page 500)
        start_time = time.time()
        
        filter_obj = UserFilter(
            client_id="perf-test",
            page=500,  # Very deep pagination
            page_size=20
        )
        
        users_page = await repository.find_all(filter_obj)
        count = await repository.count(filter_obj)
        
        duration = time.time() - start_time
        
        # Assertions
        assert len(users_page) <= 20
        assert count == 10000, f"Expected 10,000 users, got {count}"
        assert duration < 2.0, f"Deep pagination (page 500) took {duration:.2f}s, should be < 2s"
        
        print(f"✓ Deep pagination (page 500/500) with {count:,} users took {duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_search_performance_with_10k_users(self, db_session: AsyncSession):
        """
        Test search performance with 10,000 users.
        
        Full-text search should remain fast even with large datasets.
        """
        repository = AppUserRepository(db_session)
        
        # Create 10K users with searchable data
        print("\n⏳ Creating 10,000 users with searchable names...")
        await UserFactory.create_batch_persisted(db_session, count=10000, client_id="search-perf")
        print("✓ Users created")
        
        # Test search performance
        print("📊 Testing search performance...")
        start_time = time.time()
        
        filter_obj = UserFilter(
            client_id="search-perf",
            search="test",  # Common term
            page=1,
            page_size=20
        )
        
        results = await repository.find_all(filter_obj)
        
        duration = time.time() - start_time
        
        # Should be fast even with 10K users
        assert duration < 1.0, f"Search with 10K users took {duration:.2f}s, should be < 1s"
        assert len(results) <= 20
        
        print(f"✓ Search across 10,000 users completed in {duration:.3f}s")


@pytest.mark.performance
@pytest.mark.slow
class TestPermissionCheckPerformance:
    """Test permission checking performance"""
    
    @pytest.mark.asyncio
    async def test_permission_lookup_with_10k_permissions(self, db_session: AsyncSession):
        """
        Test permission lookup performance with 10,000 permissions total.
        
        Simulates system with many users and permissions.
        """
        repository = PermissionRepository(db_session)
        user_id = "user-perf-test"
        client_id = "client-perf-test"
        
        print("\n⏳ Creating 10,000 permissions across users...")
        
        # Create 10K permissions distributed across 100 users (100 perms each)
        for user_idx in range(100):
            current_user_id = f"user-{user_idx}" if user_idx > 0 else user_id
            for i in range(100):
                permission = PermissionFactory.build(
                    user_id=current_user_id,
                    client_id=client_id,
                    resource_type=f"resource-{i % 10}",  # 10 different resource types
                    resource_id=f"res-{user_idx}-{i}",
                    action=PermissionAction.READ
                )
                await repository.save(permission)
        
        await db_session.commit()
        print("✓ 10,000 permissions created")
        
        # Test lookup performance for specific user (among 10K total perms)
        print(f"📊 Testing permission lookup among 10,000 total permissions...")
        start_time = time.time()
        
        permissions = await repository.find_by_user(user_id, client_id)
        
        duration = time.time() - start_time
        
        # Assertions
        assert len(permissions) == 100, f"User should have 100 permissions, got {len(permissions)}"
        assert duration < 0.5, f"Permission lookup (10K total) took {duration:.2f}s, should be < 0.5s"
        
        print(f"✓ Found {len(permissions)} permissions among 10,000 total in {duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_permission_filtering_performance(self, db_session: AsyncSession):
        """Test filtering permissions by resource type"""
        repository = PermissionRepository(db_session)
        user_id = "user-filter-test"
        client_id = "client-filter-test"
        
        # Create permissions for different resource types
        for i in range(50):
            permission = PermissionFactory.build(
                user_id=user_id,
                client_id=client_id,
                resource_type="project" if i % 2 == 0 else "ticket",
                resource_id=f"res-{i}",
                action=PermissionAction.READ
            )
            await repository.save(permission)
        
        await db_session.commit()
        
        # Test filtering performance
        start_time = time.time()
        
        project_perms = await repository.find_by_user_and_resource_type(
            user_id,
            client_id,
            "project"
        )
        
        duration = time.time() - start_time
        
        # Assertions
        assert len(project_perms) >= 25  # Half should be projects
        assert all(p.resource_type == "project" for p in project_perms)
        assert duration < 0.3, f"Filtering took {duration:.2f}s, should be < 0.3s"
        
        print(f"✓ Filtered to {len(project_perms)} permissions in {duration:.3f}s")


@pytest.mark.performance
class TestLoginPerformance:
    """Test login performance under load"""
    
    @pytest.mark.asyncio
    async def test_login_performance_with_existing_users(self, db_session: AsyncSession):
        """Test login performance doesn't degrade with many existing users"""
        from core.services.auth.auth_service import AuthService
        from infra.redis.cache_service import get_cache_service
        from infra.config.settings_provider import SettingsProvider
        
        # Create many users in system
        repository = AppUserRepository(db_session)
        await UserFactory.create_batch_persisted(db_session, count=50)
        
        # Create specific user to login
        test_user = await UserFactory.create_persisted(
            db_session,
            email="performance@test.com",
            password="TestPass123"
        )
        
        # Setup auth service
        cache_service = await get_cache_service()
        settings_provider = SettingsProvider()
        auth_service = AuthService(repository, cache_service, settings_provider)
        
        # Test login performance
        start_time = time.time()
        
        access_token, refresh_token, user = await auth_service.login(
            email="performance@test.com",
            password="TestPass123",
            client_id="test-client-id"
        )
        
        duration = time.time() - start_time
        
        # Assertions
        assert access_token is not None
        assert user.id == test_user.id
        assert duration < 0.5, f"Login took {duration:.2f}s, should be < 0.5s"
        
        print(f"✓ Login completed in {duration:.3f}s")

