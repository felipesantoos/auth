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
    """Create test user"""
    from core.domain.auth.app_user import AppUser
    from core.domain.auth.user_role import UserRole
    from infra.database.repositories.app_user_repository import AppUserRepository
    from core.services.auth.auth_service import AuthService
    from infra.redis.cache_service import get_cache_service
    from infra.config.settings_provider import SettingsProvider
    
    repository = AppUserRepository(db_session)
    cache_service = await get_cache_service()
    settings_provider = SettingsProvider()
    auth_service = AuthService(repository, cache_service, settings_provider)
    
    user = await auth_service.register(
        username="testuser",
        email="test@example.com",
        password="TestPass123",
        name="Test User",
        client_id="test-client-id"
    )
    
    return user


@pytest.fixture
async def admin_user(db_session):
    """Create admin user"""
    from core.domain.auth.app_user import AppUser
    from core.domain.auth.user_role import UserRole
    from infra.database.repositories.app_user_repository import AppUserRepository
    import bcrypt
    
    repository = AppUserRepository(db_session)
    
    password_hash = bcrypt.hashpw("Admin123".encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    admin = AppUser(
        id=None,
        username="admin",
        email="admin@test.com",
        _password_hash=password_hash,
        name="Admin User",
        role=UserRole.ADMIN,
        client_id="test-client-id",
        active=True
    )
    
    return await repository.save(admin)


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

