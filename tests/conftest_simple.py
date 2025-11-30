# Simple conftest.py for basic pytest functionality
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from datetime import datetime

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project to path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app
from app.database import Base
from app.models import Task
from app.schemas import TaskCreate, TaskStatus

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create event loop for test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def test_client():
    """FastAPI test client."""
    from app.database import SyncSessionLocal

    def override_get_db():
        try:
            db = SyncSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[app.database.get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client(test_db_session: AsyncSession):
    """Async HTTP client for testing."""
    def override_get_db():
        return test_db_session

    app.dependency_overrides[app.database.get_db] = override_get_db

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def sample_task(test_db_session: AsyncSession) -> Task:
    """Create a sample task."""
    task = Task(
        prompt="Sample AI task for testing",
        model="deepseek-chat",
        provider="deepseek",
        priority=2,
        status=TaskStatus.PENDING
    )
    test_db_session.add(task)
    await test_db_session.commit()
    await test_db_session.refresh(task)
    return task

@pytest_asyncio.fixture
async def completed_task(test_db_session: AsyncSession) -> Task:
    """Create a completed task."""
    task = Task(
        prompt="Completed task for testing",
        model="gpt-3.5-turbo",
        provider="openai",
        priority=1,
        status=TaskStatus.COMPLETED,
        result="This is a sample AI-generated response for testing purposes."
    )
    test_db_session.add(task)
    await test_db_session.commit()
    await test_db_session.refresh(task)
    return task

@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "API_V1_PREFIX": "/api/v1",
        "TASKS_ENDPOINT": "/api/v1/tasks",
        "HEALTH_CHECK_ENDPOINT": "/api/v1/health",
    }