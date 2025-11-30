from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config_fixed import settings
import contextlib

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Convert async URL to sync URL for Celery tasks
sync_database_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# Create sync engine for Celery tasks
sync_engine = create_engine(
    sync_database_url,
    echo=settings.debug,
)

# Create sync session factory for Celery tasks
SyncSessionLocal = sessionmaker(
    sync_engine, autocommit=False, autoflush=False
)


@contextlib.contextmanager
def get_sync_db_session():
    """Get synchronous database session for Celery tasks"""
    session = SyncSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_db_session():
    """Get async database session (helper function)"""
    return AsyncSessionLocal()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models import Task

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)