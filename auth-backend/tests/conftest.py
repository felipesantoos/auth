"""
Test configuration and fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from main import app
from infra.database.database import Base, get_db_session
from config.settings import settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_system_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create database session for tests"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(db_session):
    """Create async HTTP client for API testing"""
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create test user with personal workspace (multi-workspace architecture)"""
    from core.domain.auth.app_user import AppUser
    # REMOVED: from core.domain.auth.user_role import UserRole
    from infra.database.repositories.app_user_repository import AppUserRepository
    from infra.database.repositories.workspace_repository import WorkspaceRepository
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    from core.services.auth.auth_service import AuthService
    from core.services.workspace.workspace_service import WorkspaceService
    from core.services.workspace.workspace_member_service import WorkspaceMemberService
    from infra.redis.cache_service import get_cache_service
    from infra.config.settings_provider import SettingsProvider
    
    repository = AppUserRepository(db_session)
    cache_service = await get_cache_service()
    settings_provider = SettingsProvider()
    workspace_service = WorkspaceService(WorkspaceRepository(db_session))
    workspace_member_service = WorkspaceMemberService(WorkspaceMemberRepository(db_session))
    
    auth_service = AuthService(
        repository,
        cache_service,
        settings_provider,
        workspace_service,
        workspace_member_service
    )
    
    user, workspace_id = await auth_service.register(
        username="testuser",
        email="test@example.com",
        password="TestPass123",
        name="Test User",
        workspace_name="Test Workspace"
    )
    
    return user


# REMOVED: admin_user fixture (admin is now per-workspace, not global)
# Use test_user with workspace_admin_member fixture instead

@pytest.fixture
async def test_workspace(db_session):
    """Create test workspace"""
    from tests.factories.workspace_factory import WorkspaceFactory
    from infra.database.repositories.workspace_repository import WorkspaceRepository
    
    repository = WorkspaceRepository(db_session)
    workspace = WorkspaceFactory.create_workspace(
        id=None,
        name="Test Workspace",
        slug="test-workspace"
    )
    
    return await repository.save(workspace)


@pytest.fixture
async def workspace_admin_member(db_session, test_user, test_workspace):
    """Create admin workspace membership for test_user"""
    from tests.factories.workspace_factory import WorkspaceMemberFactory
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    from core.domain.workspace.workspace_role import WorkspaceRole
    
    repository = WorkspaceMemberRepository(db_session)
    member = WorkspaceMemberFactory.create_member(
        id=None,
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        role=WorkspaceRole.ADMIN
    )
    
    return await repository.save(member)


@pytest.fixture
async def auth_token(async_client, test_user):
    """Get auth token for test user"""
    response = await async_client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123",
        "client_id": "test-client-id"
    })
    
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def admin_token(async_client, admin_user):
    """Get auth token for admin user"""
    # Login as admin
    response = await async_client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin123",
        "client_id": "test-client-id"
    })
    
    data = response.json()
    return data["access_token"]

