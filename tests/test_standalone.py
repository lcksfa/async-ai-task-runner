# Standalone API tests without conftest.py dependencies
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from typing import Dict, Any, List
from datetime import datetime
import json
import asyncio

# Direct imports
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app
from app.models import Task
from app.schemas import TaskCreate, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def test_db_session():
    """Test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda: Base.metadata.create_all(bind=test_engine))

    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(lambda: Base.metadata.drop_all(bind=test_engine))

@pytest_asyncio.fixture
async def async_client(test_db_session: AsyncSession):
    """Async HTTP client for testing."""
    def override_get_db():
        return test_db_session

    app.dependency_overrides["app.database.get_db"] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "API_V1_PREFIX": "/api/v1",
        "TASKS_ENDPOINT": "/api/v1/tasks",
        "HEALTH_CHECK_ENDPOINT": "/api/v1/health",
    }


class TestHealthCheck:
    """Test health check endpoint functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_success(self, async_client: AsyncClient, test_config):
        """Test successful health check response."""
        response = await async_client.get(f"{test_config['HEALTH_CHECK_ENDPOINT']}")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)


class TestTaskManagement:
    """Test task CRUD operations and business logic."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_success(self, async_client: AsyncClient, test_db_session, test_config):
        """Test successful task creation."""
        task_data = {
            "prompt": "What is the capital of France and provide historical context?",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "priority": 3
        }

        response = await async_client.post(
            f"{test_config['TASKS_ENDPOINT']}",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["prompt"] == task_data["prompt"]
        assert data["model"] == task_data["model"]
        assert data["provider"] == task_data["provider"]
        assert data["priority"] == task_data["priority"]
        assert data["status"] == TaskStatus.PENDING.value
        assert data["result"] is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_minimal_data(self, async_client: AsyncClient, test_config):
        """Test task creation with minimal required data."""
        task_data = {
            "prompt": "Simple test question"
        }

        response = await async_client.post(
            f"{test_config['TASKS_ENDPOINT']}",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()

        assert data["prompt"] == task_data["prompt"]
        assert data["status"] == TaskStatus.PENDING.value
        # Should use default values
        assert data["priority"] == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, async_client: AsyncClient, test_config):
        """Test getting tasks when database is empty."""
        response = await async_client.get(f"{test_config['TASKS_ENDPOINT']}")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, async_client: AsyncClient, test_config):
        """Test getting a task that doesn't exist."""
        response = await async_client.get(f"{test_config['TASKS_ENDPOINT']}/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])