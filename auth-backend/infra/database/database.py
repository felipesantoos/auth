"""
Database Configuration
SQLAlchemy async engine and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.settings import settings

# Base class for all models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncSession:
    """
    Dependency for getting database session.
    Yields a session and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """
    Initialize database - create all tables.
    Should be called on application startup.
    """
    # Import all models here to ensure they're registered with Base.metadata
    from infra.database.models.client import DBClient  # noqa: F401
    from infra.database.models.app_user import DBAppUser  # noqa: F401
    # More models will be imported as they're created
    # Tables are created via Alembic migrations, not programmatically
    pass


async def close_database():
    """
    Close database connections.
    Should be called on application shutdown.
    """
    await engine.dispose()

