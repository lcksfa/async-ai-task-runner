# 🔄 Async Functionality Tests
"""
Comprehensive async functionality tests for Async AI Task Runner.
Tests async/await patterns, concurrency, performance, and async session management.
"""

import pytest
import pytest_asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

# Application imports
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal, get_db_session
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskStatus
from app.crud import task as task_crud
from app.worker.tasks.ai_tasks import run_ai_text_generation
from conftest import (
    async_client, test_db_session, sample_task, task_factory,
    performance_monitor
)


class TestAsyncSessionManagement:
    """Test async database session management."""

    @pytest.mark.asyncio
    async def test_async_session_context_manager(self, test_db_session: AsyncSession):
        """Test that async sessions work as context managers."""
        # Should be able to use session within context
        task = Task(
            prompt="Test async session",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )
        test_db_session.add(task)
        await test_db_session.commit()

        # Session should still be usable
        result = await test_db_session.execute(
            select(Task).filter(Task.id == task.id)
        )
        retrieved_task = result.scalar_one_or_none()

        assert retrieved_task is not None
        assert retrieved_task.prompt == "Test async session"

    @pytest.mark.asyncio
    async def test_async_session_independence(self):
        """Test that async sessions are independent."""
        async with AsyncSessionLocal() as session1:
            async with AsyncSessionLocal() as session2:
                # Create task in session1
                task1 = Task(
                    prompt="Session 1 task",
                    model="gpt-3.5-turbo",
                    provider="openai",
                    priority=1,
                    status=TaskStatus.PENDING
                )
                session1.add(task1)
                await session1.commit()

                # Task should not be visible in session2
                result = await session2.execute(
                    select(Task).filter(Task.prompt == "Session 1 task")
                )
                task_from_session2 = result.scalar_one_or_none()
                assert task_from_session2 is None

                # But should be visible in session1
                result = await session1.execute(
                    select(Task).filter(Task.prompt == "Session 1 task")
                )
                task_from_session1 = result.scalar_one_or_none()
                assert task_from_session1 is not None

    @pytest.mark.asyncio
    async def test_async_session_factory(self):
        """Test async session factory function."""
        session = await get_db_session()
        try:
            assert isinstance(session, AsyncSession)

            # Should be able to perform operations
            task = Task(
                prompt="Factory test",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            assert task.id is not None
        finally:
            await session.close()

    @pytest.mark.asyncio
    async def test_async_session_rollback(self):
        """Test async session rollback on error."""
        async with AsyncSessionLocal() as session:
            # Create valid task
            valid_task = Task(
                prompt="Valid task",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            session.add(valid_task)

            # Create invalid task (this will cause error)
            invalid_task = Task(
                prompt=None,  # This should cause integrity error
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            session.add(invalid_task)

            try:
                await session.commit()
                assert False, "Expected integrity error"
            except Exception:
                await session.rollback()

                # Verify no tasks were committed
                result = await session.execute(select(Task))
                tasks = result.scalars().all()
                assert len(tasks) == 0


class TestConcurrentOperations:
    """Test concurrent async operations."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_task_creation(self, async_client, test_db_session):
        """Test creating multiple tasks concurrently."""
        task_data = {
            "prompt": "Concurrent creation test",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        # Create 20 tasks concurrently
        tasks = [
            async_client.post("/api/v1/tasks", json=task_data)
            for _ in range(20)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should succeed
        created_tasks = []
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.status_code == 201
            created_tasks.append(response.json())

        # All tasks should have unique IDs
        task_ids = [task["id"] for task in created_tasks]
        assert len(task_ids) == len(set(task_ids))  # No duplicates

        # All tasks should have PENDING status
        for task in created_tasks:
            assert task["status"] == TaskStatus.PENDING.value

        # Verify all tasks are in database
        db_response = await async_client.get("/api/v1/tasks")
        db_tasks = db_response.json()
        assert len(db_tasks) >= 20

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_task_retrieval(self, async_client, test_db_session, task_factory):
        """Test retrieving multiple tasks concurrently."""
        # Create tasks first
        created_tasks = []
        for i in range(10):
            task = task_factory(
                prompt=f"Concurrent retrieval test {i}",
                priority=i + 1
            )
            created_tasks.append(task)
        await test_db_session.commit()

        # Retrieve all tasks concurrently
        retrieval_tasks = [
            async_client.get(f"/api/v1/tasks/{task.id}")
            for task in created_tasks
        ]

        responses = await asyncio.gather(*retrieval_tasks, return_exceptions=True)

        # All retrievals should succeed
        retrieved_tasks = []
        for response in responses:
            assert not isinstance(response, Exception)
            assert response.status_code == 200
            retrieved_tasks.append(response.json())

        # Verify all tasks were retrieved correctly
        for i, task in enumerate(retrieved_tasks):
            assert task["id"] == created_tasks[i].id
            assert task["prompt"] == created_tasks[i].prompt

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_crud_operations(self, test_db_session, task_factory):
        """Test concurrent CRUD operations on database."""
        # Create multiple tasks concurrently
        creation_tasks = []
        for i in range(10):
            task = task_factory(
                prompt=f"Concurrent CRUD test {i}",
                priority=i + 1
            )
            creation_tasks.append(task_crud.create_task(test_db_session, obj_in=task))

        created_tasks = await asyncio.gather(*creation_tasks)
        await test_db_session.commit()

        assert len(created_tasks) == 10
        assert all(task.id is not None for task in created_tasks)

        # Retrieve multiple tasks concurrently
        retrieval_tasks = [
            task_crud.get_task(test_db_session, task_id=task.id)
            for task in created_tasks
        ]

        retrieved_tasks = await asyncio.gather(*retrieval_tasks)

        assert len(retrieved_tasks) == 10
        assert all(task is not None for task in retrieved_tasks)

        # Update multiple tasks concurrently
        update_tasks = []
        for task in retrieved_tasks:
            update_data = TaskUpdate(status=TaskStatus.COMPLETED, result="Concurrent update")
            update_tasks.append(
                task_crud.update_task(test_db_session, db_obj=task, obj_in=update_data)
            )

        updated_tasks = await asyncio.gather(*update_tasks)

        assert len(updated_tasks) == 10
        assert all(task.status == TaskStatus.COMPLETED for task in updated_tasks)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_same_task_operations(self, test_db_session, task_factory):
        """Test concurrent operations on the same task."""
        # Create a task
        task = task_factory(prompt="Concurrent same task test")
        await test_db_session.commit()
        task_id = task.id

        # Perform concurrent reads on the same task
        read_tasks = [
            task_crud.get_task(test_db_session, task_id=task_id)
            for _ in range(10)
        ]

        read_results = await asyncio.gather(*read_tasks)

        # All reads should return the same task
        for result in read_results:
            assert result is not None
            assert result.id == task_id
            assert result.prompt == "Concurrent same task test"

    @pytest.mark.asyncio
    async def test_async_generator_functionality(self, test_db_session, task_factory):
        """Test async generator functionality."""
        # Create an async generator for tasks
        async def task_generator(count: int) -> AsyncGenerator[Task, None]:
            for i in range(count):
                task = task_factory(prompt=f"Generator task {i}")
                yield task

        # Create tasks using generator
        async def create_tasks_from_generator(gen: AsyncGenerator[Task, None]):
            created_tasks = []
            async for task in gen:
                created_task = await task_crud.create_task(test_db_session, obj_in=TaskCreate(
                    prompt=task.prompt,
                    model=task.model,
                    provider=task.provider,
                    priority=task.priority
                ))
                created_tasks.append(created_task)
            return created_tasks

        # Use the generator
        gen = task_generator(5)
        created_tasks = await create_tasks_from_generator(gen)
        await test_db_session.commit()

        assert len(created_tasks) == 5
        assert all(task.id is not None for task in created_tasks)


class TestAsyncPerformance:
    """Test async operation performance."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_async_vs_sync_performance(self, test_db_session, performance_monitor):
        """Test async vs sync operation performance."""
        # Create tasks data
        tasks_data = [
            TaskCreate(prompt=f"Performance test {i}")
            for i in range(50)
        ]

        # Test async creation
        with performance_monitor.measure("async_creation"):
            async_creation_tasks = [
                task_crud.create_task(test_db_session, obj_in=task_data)
                for task_data in tasks_data
            ]
            await asyncio.gather(*async_creation_tasks)

        # Test sequential creation for comparison
        with performance_monitor.measure("sequential_creation"):
            for task_data in tasks_data:
                await task_crud.create_task(test_db_session, obj_in=task_data)

        measurements = performance_monitor.all_measurements()
        async_time = measurements.get("async_creation", 0)
        sequential_time = measurements.get("sequential_creation", 0)

        print(f"Async creation time: {async_time:.3f}s")
        print(f"Sequential creation time: {sequential_time:.3f}s")

        # Async should be faster (or at least not significantly slower)
        if sequential_time > 0:
            speedup = sequential_time / async_time
            print(f"Speedup: {speedup:.2f}x")
            assert speedup > 0.5  # At least 50% as fast

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_api_endpoints(self, async_client, performance_monitor):
        """Test performance of concurrent API requests."""
        task_data = {
            "prompt": "Performance test",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        # Test concurrent task creation
        with performance_monitor.measure("concurrent_api_requests"):
            requests = [
                async_client.post("/api/v1/tasks", json=task_data)
                for _ in range(20)
            ]
            responses = await asyncio.gather(*requests, return_exceptions=True)

        # Verify all requests succeeded
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) == 20

        measurements = performance_monitor.all_measurements()
        api_time = measurements.get("concurrent_api_requests", 0)

        print(f"Concurrent API requests time: {api_time:.3f}s")
        assert api_time < 10.0  # Should complete within 10 seconds

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, test_db_session, performance_monitor):
        """Test database connection pooling performance."""
        async def create_and_retrieve_task(session, prompt: str):
            # Create task
            task_in = TaskCreate(prompt=prompt)
            task = await task_crud.create_task(session, obj_in=task_in)

            # Retrieve task
            retrieved_task = await task_crud.get_task(session, task_id=task.id)

            return retrieved_task

        # Test with multiple concurrent database operations
        with performance_monitor.measure("concurrent_db_operations"):
            async with AsyncSessionLocal() as session1:
                async with AsyncSessionLocal() as session2:
                    async with AsyncSessionLocal() as session3:
                        operations = [
                            create_and_retrieve_task(session1, f"Pool test {i}")
                            if i % 3 == 0 else
                            create_and_retrieve_task(session2, f"Pool test {i}")
                            if i % 3 == 1 else
                            create_and_retrieve_task(session3, f"Pool test {i}")
                            for i in range(15)
                        ]
                        results = await asyncio.gather(*operations)

        measurements = performance_monitor.all_measurements()
        db_time = measurements.get("concurrent_db_operations", 0)

        print(f"Concurrent database operations time: {db_time:.3f}s")
        assert db_time < 15.0  # Should complete within 15 seconds

        # Verify all operations succeeded
        assert len(results) == 15
        assert all(task is not None for task in results)


class TestAsyncErrorHandling:
    """Test async error handling and recovery."""

    @pytest.mark.asyncio
    async def test_async_exception_handling(self, async_client):
        """Test proper handling of async exceptions."""
        # Test invalid JSON
        response = await async_client.post(
            "/api/v1/tasks",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test invalid task data
        response = await async_client.post(
            "/api/v1/tasks",
            json={"prompt": ""}  # Empty prompt
        )
        assert response.status_code == 422

        # Test non-existent task retrieval
        response = await async_client.get("/api/v1/tasks/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_async_timeout_handling(self, test_db_session):
        """Test handling of async operations with timeouts."""
        async def slow_operation():
            await asyncio.sleep(0.1)  # Simulate slow operation
            return "completed"

        # Test with sufficient timeout
        result = await asyncio.wait_for(slow_operation(), timeout=1.0)
        assert result == "completed"

        # Test with insufficient timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.05)

    @pytest.mark.asyncio
    async def test_async_cancellation(self, test_db_session):
        """Test handling of async operation cancellation."""
        async def long_running_operation():
            try:
                for i in range(100):
                    await asyncio.sleep(0.01)
                    # Check if task is cancelled
                    if asyncio.current_task().cancelled():
                        raise asyncio.CancelledError()
                return "completed"
            except asyncio.CancelledError:
                return "cancelled"

        # Start the operation
        task = asyncio.create_task(long_running_operation())

        # Cancel after a short delay
        await asyncio.sleep(0.05)
        task.cancel()

        # Wait for cancellation to take effect
        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_async_partial_failure_recovery(self, async_client):
        """Test recovery from partial failures in concurrent operations."""
        task_data = {
            "prompt": "Test prompt",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        # Mix of valid and invalid requests
        requests = [
            async_client.post("/api/v1/tasks", json=task_data),  # Valid
            async_client.post("/api/v1/tasks", json={"prompt": ""}),  # Invalid
            async_client.post("/api/v1/tasks", json=task_data),  # Valid
            async_client.post("/api/v1/tasks", content="invalid"),  # Invalid
            async_client.post("/api/v1/tasks", json=task_data),  # Valid
        ]

        responses = await asyncio.gather(*requests, return_exceptions=True)

        # Handle partial failures gracefully
        successful = []
        failed = []

        for response in responses:
            if isinstance(response, Exception):
                failed.append(response)
            elif hasattr(response, 'status_code') and response.status_code == 201:
                successful.append(response)
            else:
                failed.append(response)

        # Should have some successes and some failures
        assert len(successful) == 3
        assert len(failed) == 2

        # Verify successful tasks were created
        for response in successful:
            data = response.json()
            assert data["prompt"] == task_data["prompt"]
            assert data["status"] == TaskStatus.PENDING.value


class TestCeleryAsyncIntegration:
    """Test integration between async FastAPI and synchronous Celery."""

    @pytest.mark.asyncio
    @patch('app.worker.tasks.ai_tasks.ai_service')
    async def test_celery_task_with_async_ai_service(self, mock_ai_service, test_db_session):
        """Test that Celery task correctly calls async AI service."""
        # Setup mock AI service
        mock_ai_service.is_available.return_value = True
        mock_ai_service.generate_text = AsyncMock(return_value="Mock AI response")

        # Create a task in database
        task_in = TaskCreate(
            prompt="Test Celery async integration",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1
        )
        task = await task_crud.create_task(test_db_session, obj_in=task_in)
        await test_db_session.commit()

        # Mock Celery task (run synchronously for testing)
        result = run_ai_text_generation(
            task_id=str(task.id),
            prompt=task.prompt,
            model=task.model,
            provider=task.provider
        )

        # Verify AI service was called
        mock_ai_service.is_available.assert_called_once()
        mock_ai_service.generate_text.assert_called_once_with(
            prompt=task.prompt,
            provider_name=task.provider,
            model=task.model,
            temperature=0.7,  # Default temperature
            max_tokens=1000   # Default max tokens
        )

        # Verify result structure
        assert result['task_id'] == str(task.id)
        assert result['status'] == 'completed'
        assert result['result'] == "Mock AI response"
        assert 'processing_time' in result
        assert result['provider_used'] == task.provider

        # Verify task was updated in database
        updated_task = await task_crud.get_task(test_db_session, task_id=task.id)
        assert updated_task is not None
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.result == "Mock AI response"

    @pytest.mark.asyncio
    @patch('app.worker.tasks.ai_tasks.ai_service')
    async def test_celery_task_with_ai_service_failure(self, mock_ai_service, test_db_session):
        """Test Celery task behavior when AI service fails."""
        # Setup mock AI service to raise exception
        mock_ai_service.is_available.return_value = True
        mock_ai_service.generate_text = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )

        # Create a task in database
        task_in = TaskCreate(
            prompt="Test Celery failure",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1
        )
        task = await task_crud.create_task(test_db_session, obj_in=task_in)
        await test_db_session.commit()

        # Run Celery task (should use fallback)
        result = run_ai_text_generation(
            task_id=str(task.id),
            prompt=task.prompt,
            model=task.model,
            provider=task.provider
        )

        # Verify task was completed with fallback result
        assert result['task_id'] == str(task.id)
        assert result['status'] == 'completed'
        assert result['result'] is not None
        assert len(result['result']) > 0

        # Verify task was updated in database
        updated_task = await task_crud.get_task(test_db_session, task_id=task.id)
        assert updated_task is not None
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.result is not None

    @pytest.mark.asyncio
    @patch('app.worker.tasks.ai_tasks.ai_service')
    async def test_celery_task_with_no_ai_service(self, mock_ai_service, test_db_session):
        """Test Celery task behavior when no AI service is available."""
        # Setup mock AI service as unavailable
        mock_ai_service.is_available.return_value = False

        # Create a task in database
        task_in = TaskCreate(
            prompt="Test no AI service",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1
        )
        task = await task_crud.create_task(test_db_session, obj_in=task_in)
        await test_db_session.commit()

        # Run Celery task (should fail immediately)
        with pytest.raises(Exception):
            run_ai_text_generation(
                task_id=str(task.id),
                prompt=task.prompt,
                model=task.model,
                provider=task.provider
            )

        # Verify task was marked as failed
        updated_task = await task_crud.get_task(test_db_session, task_id=task.id)
        assert updated_task is not None
        assert updated_task.status == TaskStatus.FAILED
        assert "没有可用的AI服务" in updated_task.result


class TestAsyncContextManagers:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager_usage(self, test_db_session):
        """Test async context manager patterns."""
        @asynccontextmanager
        async def task_transaction():
            """Custom async context manager for task operations."""
            try:
                print("Starting transaction")
                yield test_db_session
                await test_db_session.commit()
                print("Transaction committed")
            except Exception as e:
                await test_db_session.rollback()
                print(f"Transaction rolled back: {e}")
                raise

        # Use the custom context manager
        async with task_transaction() as session:
            task = Task(
                prompt="Context manager test",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            session.add(task)

        # Verify task was committed
        result = await test_db_session.execute(
            select(Task).filter(Task.prompt == "Context manager test")
        )
        created_task = result.scalar_one_or_none()
        assert created_task is not None

    @pytest.mark.asyncio
    async def test_nested_async_context_managers(self, test_db_session):
        """Test nested async context managers."""
        @asynccontextmanager
        async def outer_context():
            print("Entering outer context")
            yield test_db_session
            print("Exiting outer context")

        @asynccontextmanager
        async def inner_context(session):
            print("Entering inner context")
            try:
                yield session
                await session.commit()
                print("Inner context committed")
            except Exception:
                await session.rollback()
                print("Inner context rolled back")
                raise

        # Test nested context managers
        async with outer_context() as session:
            async with inner_context(session) as inner_session:
                task = Task(
                    prompt="Nested context test",
                    model="gpt-3.5-turbo",
                    provider="openai",
                    priority=1,
                    status=TaskStatus.PENDING
                )
                inner_session.add(task)

        # Verify task was committed
        result = await test_db_session.execute(
            select(Task).filter(Task.prompt == "Nested context test")
        )
        created_task = result.scalar_one_or_none()
        assert created_task is not None


class TestAsyncResourceManagement:
    """Test async resource management and cleanup."""

    @pytest.mark.asyncio
    async def test_async_resource_cleanup(self):
        """Test that async resources are properly cleaned up."""
        resources_created = []
        resources_cleaned = []

        async def create_resource(name: str):
            resources_created.append(name)
            return {"name": name, "created_at": datetime.utcnow()}

        async def cleanup_resource(resource):
            resources_cleaned.append(resource["name"])

        @asynccontextmanager
        async def managed_resource(name: str):
            resource = await create_resource(name)
            try:
                yield resource
            finally:
                await cleanup_resource(resource)

        # Use managed resource
        async with managed_resource("test_resource") as resource:
            assert resource["name"] == "test_resource"
            assert "test_resource" in resources_created
            assert "test_resource" not in resources_cleaned

        # Resource should be cleaned up after context
        assert "test_resource" in resources_cleaned

    @pytest.mark.asyncio
    async def test_async_session_cleanup(self):
        """Test async session cleanup."""
        sessions_created = []
        sessions_closed = []

        # Patch session creation to track lifecycle
        original_init = AsyncSessionLocal.__init__

        def tracked_init(self, *args, **kwargs):
            sessions_created.append(self)
            return original_init(self, *args, **kwargs)

        AsyncSessionLocal.__init__ = tracked_init

        try:
            # Create and use sessions
            async with AsyncSessionLocal() as session1:
                pass
            async with AsyncSessionLocal() as session2:
                pass

            # Sessions should be created
            assert len(sessions_created) == 2

        finally:
            # Restore original init
            AsyncSessionLocal.__init__ = original_init

        # Sessions should be automatically closed by context manager


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])