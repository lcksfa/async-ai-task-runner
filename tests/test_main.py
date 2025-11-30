# 🧪 API Integration Tests
"""
Comprehensive API endpoint tests for Async AI Task Runner.
Tests all CRUD operations, validation, error handling, and business logic.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from typing import Dict, Any, List
from datetime import datetime
import json
import asyncio

# Application imports
from app.models import Task
from app.schemas import TaskCreate, TaskStatus, TaskResponse
from app.crud import task as task_crud
from conftest import (
    test_client, async_client, test_db_session, sample_task_create,
    sample_task, completed_task, failed_task, test_config
)


class TestHealthCheck:
    """Test health check endpoint functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_success(self, async_client: AsyncClient):
        """Test successful health check response."""
        response = await async_client.get(f"{test_config['API_V1_PREFIX']}/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    @pytest.mark.unit
    def test_health_check_sync(self, test_client: TestClient):
        """Test health check with synchronous client."""
        response = test_client.get(f"{test_config['API_V1_PREFIX']}/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_health_check_headers(self, async_client: AsyncClient):
        """Test health check response headers."""
        response = await async_client.get(f"{test_config['API_V1_PREFIX']}/health")

        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]


class TestTaskManagement:
    """Test task CRUD operations and business logic."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_success(self, async_client: AsyncClient, test_db_session):
        """Test successful task creation."""
        task_data = {
            "prompt": "What is the capital of France and provide historical context?",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "priority": 3
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
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

        # Verify timestamp format
        assert isinstance(data["created_at"], str)
        datetime.fromisoformat(data["created_at"])  # Will raise if invalid

        # Verify task was actually created in database
        db_task = await task_crud.get_task(test_db_session, task_id=data["id"])
        assert db_task is not None
        assert db_task.prompt == task_data["prompt"]
        assert db_task.status == TaskStatus.PENDING

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_minimal_data(self, async_client: AsyncClient, test_db_session):
        """Test task creation with minimal required data."""
        task_data = {
            "prompt": "Simple test question"
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()

        assert data["prompt"] == task_data["prompt"]
        assert data["status"] == TaskStatus.PENDING.value
        # Should use default values
        assert data["priority"] == 1
        assert data["model"] is None
        assert data["provider"] is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_invalid_prompt_empty(self, async_client: AsyncClient):
        """Test task creation with empty prompt."""
        task_data = {
            "prompt": "",
            "model": "gpt-3.5-turbo"
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["type"] == "value_error"
        assert "prompt" in str(error_detail["msg"]).lower()
        assert "at least 1 character" in str(error_detail["msg"]).lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_invalid_prompt_too_long(self, async_client: AsyncClient):
        """Test task creation with prompt too long."""
        task_data = {
            "prompt": "x" * 1001,  # Exceeds 1000 character limit
            "model": "gpt-3.5-turbo"
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["type"] == "value_error"
        assert "prompt" in str(error_detail["msg"]).lower()
        assert "1000" in str(error_detail["msg"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_invalid_priority_too_low(self, async_client: AsyncClient):
        """Test task creation with priority too low."""
        task_data = {
            "prompt": "Test prompt",
            "priority": 0  # Below minimum of 1
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["type"] == "value_error"
        assert "priority" in str(error_detail["msg"]).lower()
        assert "1" in str(error_detail["msg"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_invalid_priority_too_high(self, async_client: AsyncClient):
        """Test task creation with priority too high."""
        task_data = {
            "prompt": "Test prompt",
            "priority": 11  # Above maximum of 10
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert error_detail["type"] == "value_error"
        assert "priority" in str(error_detail["msg"]).lower()
        assert "10" in str(error_detail["msg"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, async_client: AsyncClient, test_db_session):
        """Test getting tasks when database is empty."""
        response = await async_client.get(f"{test_config['API_V1_PREFIX']}/tasks")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_tasks_with_data(self, async_client: AsyncClient, test_db_session_with_data):
        """Test getting tasks when database has data."""
        response = await async_client.get(f"{test_config['API_V1_PREFIX']}/tasks")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 4  # We created 4 sample tasks

        # Verify structure of each task
        for task in data:
            assert "id" in task
            assert "prompt" in task
            assert "model" in task
            assert "provider" in task
            assert "status" in task
            assert "priority" in task
            assert "created_at" in task

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_tasks_with_pagination(self, async_client: AsyncClient, test_db_session_with_data):
        """Test task pagination functionality."""
        # Test limit parameter
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks?limit=2"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

        # Test skip parameter
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks?skip=2"
        )

        assert response.status_code == 200
        data = response.json()
        # Should return fewer tasks since we skipped first 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_success(self, async_client: AsyncClient, sample_task: Task):
        """Test getting a specific task by ID."""
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/{sample_task.id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_task.id
        assert data["prompt"] == sample_task.prompt
        assert data["model"] == sample_task.model
        assert data["provider"] == sample_task.provider
        assert data["status"] == sample_task.status.value
        assert data["priority"] == sample_task.priority

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, async_client: AsyncClient):
        """Test getting a task that doesn't exist."""
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/99999"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_completed_task(self, async_client: AsyncClient, completed_task: Task):
        """Test getting a completed task with result."""
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/{completed_task.id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == TaskStatus.COMPLETED.value
        assert data["result"] == completed_task.result
        assert "updated_at" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_failed_task(self, async_client: AsyncClient, failed_task: Task):
        """Test getting a failed task."""
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/{failed_task.id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == TaskStatus.FAILED.value
        assert data["result"] == failed_task.result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_task_lifecycle_complete_flow(self, async_client: AsyncClient, test_db_session):
        """Test complete task lifecycle from creation to completion."""
        # 1. Create task
        task_data = {
            "prompt": "What is Python async/await and how does it work?",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "priority": 2
        }

        create_response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 2. Verify initial status
        assert created_task["status"] == TaskStatus.PENDING.value

        # 3. Get task to confirm it exists
        get_response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/{task_id}"
        )

        assert get_response.status_code == 200
        retrieved_task = get_response.json()
        assert retrieved_task["id"] == task_id
        assert retrieved_task["status"] == TaskStatus.PENDING.value

        # 4. Simulate task completion (update in database directly)
        # In real scenario, this would be done by Celery worker
        from app.crud.task import update_task
        from app.schemas import TaskUpdate

        task_update = TaskUpdate(
            status=TaskStatus.COMPLETED,
            result="Async/await is Python's syntax for asynchronous programming..."
        )

        db_task = await task_crud.get_task(test_db_session, task_id=task_id)
        await update_task(db=test_db_session, db_obj=db_task, obj_in=task_update)

        # 5. Verify updated status
        final_response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/{task_id}"
        )

        assert final_response.status_code == 200
        final_task = final_response.json()
        assert final_task["status"] == TaskStatus.COMPLETED.value
        assert final_task["result"] is not None
        assert "updated_at" in final_task


class TestConcurrentOperations:
    """Test concurrent API operations."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_task_creation(self, async_client: AsyncClient):
        """Test creating multiple tasks concurrently."""
        import asyncio

        task_data = {
            "prompt": "Concurrent test task",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        # Create 10 tasks concurrently
        tasks = [
            async_client.post(
                f"{test_config['API_V1_PREFIX']}/tasks",
                json=task_data
            )
            for _ in range(10)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all requests succeeded
        created_tasks = []
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.status_code == 201
            created_tasks.append(response.json())

        # Verify all tasks have unique IDs
        task_ids = [task["id"] for task in created_tasks]
        assert len(task_ids) == len(set(task_ids))  # All IDs should be unique

        # Verify all tasks have PENDING status
        for task in created_tasks:
            assert task["status"] == TaskStatus.PENDING.value

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_task_retrieval(self, async_client: AsyncClient, test_db_session_with_data):
        """Test retrieving multiple tasks concurrently."""
        import asyncio

        # First, create some tasks
        tasks = []
        for i in range(5):
            task_data = {
                "prompt": f"Concurrent test task {i}",
                "model": "gpt-3.5-turbo",
                "priority": i + 1
            }
            response = await async_client.post(
                f"{test_config['API_V1_PREFIX']}/tasks",
                json=task_data
            )
            tasks.append(response.json())

        # Retrieve all tasks concurrently
        retrieval_tasks = [
            async_client.get(f"{test_config['API_V1_PREFIX']}/tasks/{task['id']}")
            for task in tasks
        ]

        responses = await asyncio.gather(*retrieval_tasks, return_exceptions=True)

        # Verify all retrievals succeeded
        retrieved_tasks = []
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.status_code == 200
            retrieved_tasks.append(response.json())

        # Verify all tasks were retrieved correctly
        for i, task in enumerate(retrieved_tasks):
            assert task["id"] == tasks[i]["id"]
            assert task["prompt"] == tasks[i]["prompt"]


class TestErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_json_request(self, async_client: AsyncClient):
        """Test handling of invalid JSON in request body."""
        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """Test handling of missing required fields."""
        # Missing prompt field
        task_data = {
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert "prompt" in str(error_detail["msg"]).lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unexpected_fields(self, async_client: AsyncClient):
        """Test handling of unexpected fields in request."""
        task_data = {
            "prompt": "Test prompt",
            "model": "gpt-3.5-turbo",
            "unexpected_field": "should be ignored"
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        # Should succeed and ignore unexpected field
        assert response.status_code == 201
        data = response.json()
        assert data["prompt"] == task_data["prompt"]
        assert "unexpected_field" not in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_task_id_type(self, async_client: AsyncClient):
        """Test handling of invalid task ID type."""
        response = await async_client.get(
            f"{test_config['API_V1_PREFIX']}/tasks/invalid_id"
        )

        # FastAPI should handle this as 422 (validation error)
        assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_payload(self, async_client: AsyncClient):
        """Test handling of request payload at size limits."""
        # Create prompt at maximum allowed size
        task_data = {
            "prompt": "x" * 1000,  # Maximum allowed size
            "model": "gpt-3.5-turbo",
            "priority": 5
        }

        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["prompt"]) == 1000


class TestResponseHeadersAndCORS:
    """Test response headers and CORS configuration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_response_content_type(self, async_client: AsyncClient):
        """Test that all endpoints return correct content type."""
        endpoints = [
            (f"{test_config['API_V1_PREFIX']}/health", "GET"),
            (f"{test_config['API_V1_PREFIX']}/tasks", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.post(endpoint, json={})

            assert "content-type" in response.headers
            assert "application/json" in response.headers["content-type"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are present."""
        response = await async_client.options(
            f"{test_config['API_V1_PREFIX']}/tasks",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        assert response.status_code == 200


class TestAPIPerformance:
    """Test API performance and response times."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_api_response_times(self, async_client: AsyncClient, performance_monitor):
        """Test API response times are within acceptable limits."""
        import time

        # Test health check
        with performance_monitor.measure("health_check"):
            response = await async_client.get(f"{test_config['API_V1_PREFIX']}/health")
            assert response.status_code == 200

        # Test task creation
        task_data = {
            "prompt": "Performance test prompt",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        with performance_monitor.measure("task_creation"):
            response = await async_client.post(
                f"{test_config['API_V1_PREFIX']}/tasks",
                json=task_data
            )
            assert response.status_code == 201

        # Test task retrieval
        response = await async_client.get(f"{test_config['API_V1_PREFIX']}/tasks")
        assert response.status_code == 200

        with performance_monitor.measure("task_retrieval"):
            response = await async_client.get(f"{test_config['API_V1_PREFIX']}/tasks")
            assert response.status_code == 200

        # Check performance (all operations should be under 1 second)
        measurements = performance_monitor.all_measurements()
        for operation, duration in measurements.items():
            assert duration < 1.0, f"{operation} took {duration:.3f}s, expected < 1.0s"


# Test data validation utilities
@pytest.fixture
def valid_task_data():
    """Valid task data for testing."""
    return {
        "prompt": "What is machine learning?",
        "model": "gpt-3.5-turbo",
        "provider": "openai",
        "priority": 3
    }


@pytest.fixture
def task_data_variations():
    """Various valid task data variations."""
    return [
        {
            "prompt": "Simple question",
        },
        {
            "prompt": "Question with model",
            "model": "deepseek-chat"
        },
        {
            "prompt": "Question with all fields",
            "model": "claude-3-sonnet-20240229",
            "provider": "anthropic",
            "priority": 5
        },
        {
            "prompt": "Question with max priority",
            "priority": 10
        },
        {
            "prompt": "Question with min priority",
            "priority": 1
        }
    ]


@pytest.fixture
def invalid_task_data():
    """Invalid task data for validation testing."""
    return [
        {
            "prompt": "",  # Empty prompt
            "model": "gpt-3.5-turbo"
        },
        {
            "prompt": "x" * 1001,  # Too long prompt
            "model": "gpt-3.5-turbo"
        },
        {
            "prompt": "Valid prompt",
            "priority": 0  # Priority too low
        },
        {
            "prompt": "Valid prompt",
            "priority": 11  # Priority too high
        }
    ]


class TestTaskDataValidation:
    """Comprehensive task data validation tests."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("task_data", [
        {"prompt": "Simple question"},
        {"prompt": "Question with model", "model": "deepseek-chat"},
        {"prompt": "Question with all fields", "model": "claude-3-sonnet", "provider": "anthropic", "priority": 5},
    ])
    async def test_valid_task_data_variations(self, async_client: AsyncClient, task_data):
        """Test various valid task data combinations."""
        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["prompt"] == task_data["prompt"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("task_data,expected_error", [
        ({"prompt": ""}, "prompt"),
        ({"prompt": "x" * 1001}, "1000"),
        ({"priority": 0}, "1"),
        ({"priority": 11}, "10"),
    ])
    async def test_invalid_task_data_variations(self, async_client: AsyncClient, task_data, expected_error):
        """Test various invalid task data combinations."""
        response = await async_client.post(
            f"{test_config['API_V1_PREFIX']}/tasks",
            json=task_data
        )

        assert response.status_code == 422
        error_detail = response.json()["detail"][0]
        assert expected_error in str(error_detail["msg"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])