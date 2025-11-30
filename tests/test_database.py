# 🗄️ Database Integration Tests
"""
Comprehensive database layer tests for Async AI Task Runner.
Tests SQLAlchemy models, CRUD operations, transactions, and data integrity.
"""

import pytest
import pytest_asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import asyncio
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

# Application imports
from app.database import init_db, get_db_session, AsyncSessionLocal, Base
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskStatus
from app.crud import task as task_crud
from conftest import test_db_session, TaskFactory


class TestDatabaseConfiguration:
    """Test database configuration and initialization."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """Test database can be initialized correctly."""
        # Use a separate in-memory database for this test
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.pool import StaticPool

        test_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verify tables were created by checking if we can use them
        async with AsyncSession(test_engine) as session:
            # Create a task to verify database works
            task = Task(
                prompt="Test prompt for database initialization",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            assert task.id is not None
            assert task.created_at is not None

        await test_engine.dispose()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_database_session_creation(self):
        """Test async database session creation."""
        session = await get_db_session()
        try:
            # Verify session is created and is functional
            assert isinstance(session, AsyncSession)

            # Test simple query
            result = await session.execute(select(Task).limit(1))
            tasks = result.scalars().all()
            assert isinstance(tasks, list)
        finally:
            await session.close()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_database_session_isolation(self):
        """Test that database sessions are properly isolated."""
        async with AsyncSessionLocal() as session1:
            async with AsyncSessionLocal() as session2:
                # Create task in session1
                task1 = Task(
                    prompt="Task in session1",
                    model="gpt-3.5-turbo",
                    provider="openai",
                    priority=1,
                    status=TaskStatus.PENDING
                )
                session1.add(task1)
                await session1.commit()

                # Task should not be visible in session2 yet
                result = await session2.execute(
                    select(Task).filter(Task.prompt == "Task in session1")
                )
                task_from_session2 = result.scalar_one_or_none()
                assert task_from_session2 is None

                # But should be visible in session1
                await session1.refresh(task1)
                assert task1.prompt == "Task in session1"


class TestTaskModel:
    """Test SQLAlchemy Task model validation and behavior."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_model_creation(self, test_db_session: AsyncSession):
        """Test creating Task model instance."""
        task = Task(
            prompt="Test task creation",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=5,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task)
        await test_db_session.commit()
        await test_db_session.refresh(task)

        assert task.id is not None
        assert task.prompt == "Test task creation"
        assert task.model == "gpt-3.5-turbo"
        assert task.provider == "openai"
        assert task.priority == 5
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.created_at is not None
        assert isinstance(task.created_at, datetime)
        assert task.updated_at is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_model_default_values(self, test_db_session: AsyncSession):
        """Test Task model default values."""
        task = Task(
            prompt="Test defaults",
            status=TaskStatus.PENDING
        )

        test_db_session.add(task)
        await test_db_session.commit()
        await test_db_session.refresh(task)

        # Check defaults
        assert task.priority == 1  # Default priority
        assert task.model is None   # Can be None
        assert task.provider is None  # Can be None
        assert task.result is None   # Default is None
        assert task.status == TaskStatus.PENDING

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_model_string_length_validation(self, test_db_session: AsyncSession):
        """Test Task model prompt length validation at database level."""
        # Test maximum length (should work)
        long_prompt = "x" * 1000
        task = Task(
            prompt=long_prompt,
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task)
        await test_db_session.commit()
        await test_db_session.refresh(task)

        assert len(task.prompt) == 1000

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_model_timestamps(self, test_db_session: AsyncSession):
        """Test Task model timestamp behavior."""
        created_time = datetime.utcnow()

        task = Task(
            prompt="Test timestamps",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task)
        await test_db_session.commit()
        await test_db_session.refresh(task)

        # Verify created_at is close to creation time
        time_diff = abs((task.created_at - created_time).total_seconds())
        assert time_diff < 5  # Within 5 seconds

        # Update task to test updated_at
        original_updated_at = task.updated_at
        await asyncio.sleep(0.1)  # Small delay to ensure timestamp changes

        task.status = TaskStatus.COMPLETED
        task.result = "Test result"

        await test_db_session.commit()
        await test_db_session.refresh(task)

        assert task.updated_at > original_updated_at

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_task_model_equality(self, test_db_session: AsyncSession):
        """Test Task model equality comparison."""
        task1 = Task(
            prompt="Test equality 1",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        task2 = Task(
            prompt="Test equality 2",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task1)
        test_db_session.add(task2)
        await test_db_session.commit()
        await test_db_session.refresh(task1)
        await test_db_session.refresh(task2)

        # Different instances, different IDs
        assert task1 != task2
        assert task1.id != task2.id

        # Same task instance equals itself
        assert task1 == task1

        # Retrieve same task from database
        retrieved_task = await task_crud.get_task(test_db_session, task1.id)
        assert retrieved_task == task1
        assert retrieved_task.id == task1.id


class TestTaskCRUD:
    """Test Task CRUD operations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task(self, test_db_session: AsyncSession):
        """Test creating a task through CRUD."""
        task_in = TaskCreate(
            prompt="Test CRUD create",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=3
        )

        task = await task_crud.create_task(db=test_db_session, obj_in=task_in)

        assert task.id is not None
        assert task.prompt == task_in.prompt
        assert task.model == task_in.model
        assert task.provider == task_in.provider
        assert task.priority == task_in.priority
        assert task.status == TaskStatus.PENDING
        assert task.created_at is not None
        assert task.updated_at is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_minimal(self, test_db_session: AsyncSession):
        """Test creating a task with minimal required data."""
        task_in = TaskCreate(
            prompt="Test minimal create"
        )

        task = await task_crud.create_task(db=test_db_session, obj_in=task_in)

        assert task.id is not None
        assert task.prompt == task_in.prompt
        assert task.model is None
        assert task.provider is None
        assert task.priority == 1  # Default value
        assert task.status == TaskStatus.PENDING

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, test_db_session: AsyncSession):
        """Test retrieving a task by ID."""
        # First create a task
        task_in = TaskCreate(
            prompt="Test CRUD get",
            model="deepseek-chat",
            provider="deepseek",
            priority=2
        )
        created_task = await task_crud.create_task(db=test_db_session, obj_in=task_in)

        # Now retrieve it
        retrieved_task = await task_crud.get_task(test_db_session, created_task.id)

        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.prompt == task_in.prompt
        assert retrieved_task.model == task_in.model
        assert retrieved_task.provider == task_in.provider
        assert retrieved_task.priority == task_in.priority

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, test_db_session: AsyncSession):
        """Test retrieving a non-existent task."""
        task = await task_crud.get_task(test_db_session, task_id=99999)
        assert task is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_tasks_with_pagination(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test retrieving multiple tasks with pagination."""
        # Create multiple tasks
        tasks = []
        for i in range(15):
            task = task_factory(
                prompt=f"Test task {i+1}",
                priority=i % 5 + 1  # Priorities 1-5
            )
            tasks.append(task)

        await test_db_session.commit()

        # Test first page
        page1 = await task_crud.get_tasks(test_db_session, skip=0, limit=5)
        assert len(page1) == 5

        # Test second page
        page2 = await task_crud.get_tasks(test_db_session, skip=5, limit=5)
        assert len(page2) == 5

        # Verify no overlap
        page1_ids = {task.id for task in page1}
        page2_ids = {task.id for task in page2}
        assert page1_ids.isdisjoint(page2_ids)

        # Test tasks are ordered by created_at descending
        all_tasks = page1 + page2
        for i in range(len(all_tasks) - 1):
            assert all_tasks[i].created_at >= all_tasks[i+1].created_at

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_task(self, test_db_session: AsyncSession):
        """Test updating a task."""
        # Create task
        task_in = TaskCreate(
            prompt="Original prompt",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1
        )
        task = await task_crud.create_task(db=test_db_session, obj_in=task_in)

        # Update task
        update_data = TaskUpdate(
            prompt="Updated prompt",
            status=TaskStatus.COMPLETED,
            result="Task completed successfully"
        )
        updated_task = await task_crud.update_task(
            db=test_db_session,
            db_obj=task,
            obj_in=update_data
        )

        assert updated_task.id == task.id
        assert updated_task.prompt == "Updated prompt"
        assert updated_task.model == "gpt-3.5-turbo"  # Unchanged
        assert updated_task.provider == "openai"  # Unchanged
        assert updated_task.priority == 1  # Unchanged
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.result == "Task completed successfully"
        assert updated_task.updated_at > task.updated_at

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_task_partial(self, test_db_session: AsyncSession):
        """Test updating task with partial data."""
        # Create task
        task_in = TaskCreate(
            prompt="Original prompt",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1
        )
        task = await task_crud.create_task(db=test_db_session, obj_in=task_in)

        # Update only status
        update_data = TaskUpdate(
            status=TaskStatus.PROCESSING
        )
        updated_task = await task_crud.update_task(
            db=test_db_session,
            db_obj=task,
            obj_in=update_data
        )

        assert updated_task.prompt == "Original prompt"  # Unchanged
        assert updated_task.model == "gpt-3.5-turbo"  # Unchanged
        assert updated_task.provider == "openai"  # Unchanged
        assert updated_task.priority == 1  # Unchanged
        assert updated_task.status == TaskStatus.PROCESSING

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_task(self, test_db_session: AsyncSession):
        """Test deleting a task."""
        # Create task
        task_in = TaskCreate(
            prompt="Task to delete",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1
        )
        task = await task_crud.create_task(db=test_db_session, obj_in=task_in)

        task_id = task.id

        # Delete task
        result = await task_crud.delete_task(test_db_session, task_id=task_id)
        assert result is True

        # Verify task is deleted
        deleted_task = await task_crud.get_task(test_db_session, task_id=task_id)
        assert deleted_task is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(self, test_db_session: AsyncSession):
        """Test deleting a non-existent task."""
        result = await task_crud.delete_task(test_db_session, task_id=99999)
        assert result is False


class TestAdvancedCRUDOperations:
    """Test advanced CRUD operations used by MCP and statistics."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test filtering tasks by status and time."""
        # Create tasks with different statuses
        now = datetime.utcnow()

        pending_task = task_factory(
            prompt="Pending task",
            status=TaskStatus.PENDING,
            created_at=now - timedelta(hours=2)
        )

        processing_task = task_factory(
            prompt="Processing task",
            status=TaskStatus.PROCESSING,
            created_at=now - timedelta(hours=1)
        )

        completed_task = task_factory(
            prompt="Completed task",
            status=TaskStatus.COMPLETED,
            created_at=now - timedelta(minutes=30)
        )

        failed_task = task_factory(
            prompt="Failed task",
            status=TaskStatus.FAILED,
            created_at=now - timedelta(minutes=15)
        )

        await test_db_session.commit()

        # Test filter by status
        completed_tasks = await task_crud.get_tasks_with_filters(
            test_db_session,
            status="COMPLETED"
        )
        assert len(completed_tasks) == 1
        assert completed_tasks[0].status == TaskStatus.COMPLETED

        # Test filter by time
        recent_tasks = await task_crud.get_tasks_with_filters(
            test_db_session,
            created_after=now - timedelta(hours=1)
        )
        assert len(recent_tasks) >= 2  # Completed and failed tasks

        # Test filter by status and time
        recent_completed_tasks = await task_crud.get_tasks_with_filters(
            test_db_session,
            status="COMPLETED",
            created_after=now - timedelta(hours=1)
        )
        assert len(recent_completed_tasks) == 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_total_task_count(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test getting total task count."""
        # Create tasks
        for i in range(7):
            task_factory(prompt=f"Task {i+1}")

        await test_db_session.commit()

        count = await task_crud.get_total_task_count(test_db_session)
        assert count >= 7

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_counts_by_status(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test getting task counts grouped by status."""
        # Create tasks with different statuses
        for _ in range(3):
            task_factory(status=TaskStatus.PENDING)
        for _ in range(2):
            task_factory(status=TaskStatus.PROCESSING)
        for _ in range(4):
            task_factory(status=TaskStatus.COMPLETED)
        for _ in range(1):
            task_factory(status=TaskStatus.FAILED)

        await test_db_session.commit()

        status_counts = await task_crud.get_task_counts_by_status(test_db_session)

        # Should return Task objects with count data
        assert isinstance(status_counts, list)
        assert len(status_counts) > 0

        # Check that we have expected statuses
        statuses = [task.status for task in status_counts]
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.COMPLETED in statuses

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_model_usage_stats(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test getting model usage statistics."""
        # Create tasks with different models
        for _ in range(3):
            task_factory(model="gpt-3.5-turbo", status=TaskStatus.COMPLETED)
        for _ in range(2):
            task_factory(model="deepseek-chat", status=TaskStatus.COMPLETED)
        for _ in range(1):
            task_factory(model="claude-3-sonnet", status=TaskStatus.COMPLETED)
        for _ in range(2):
            task_factory(model="gpt-3.5-turbo", status=TaskStatus.FAILED)

        await test_db_session.commit()

        stats = await task_crud.get_model_usage_stats(test_db_session)

        assert isinstance(stats, dict)
        assert "gpt-3.5-turbo" in stats
        assert "deepseek-chat" in stats
        assert "claude-3-sonnet" in stats

        # Check stats structure
        gpt_stats = stats["gpt-3.5-turbo"]
        assert hasattr(gpt_stats, 'total_tasks')
        assert hasattr(gpt_stats, 'completed_tasks')
        assert gpt_stats.total_tasks == 5  # 3 completed + 2 failed
        assert gpt_stats.completed_tasks == 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_recent_tasks(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test getting recent tasks within time window."""
        now = datetime.utcnow()

        # Create tasks with different timestamps
        old_task = task_factory(
            prompt="Old task",
            created_at=now - timedelta(hours=25)  # Outside 24h window
        )

        recent_task1 = task_factory(
            prompt="Recent task 1",
            created_at=now - timedelta(hours=12)
        )

        recent_task2 = task_factory(
            prompt="Recent task 2",
            created_at=now - timedelta(hours=6)
        )

        very_recent_task = task_factory(
            prompt="Very recent task",
            created_at=now - timedelta(minutes=30)
        )

        await test_db_session.commit()

        # Get recent tasks (default 24 hours)
        recent_tasks = await task_crud.get_recent_tasks(test_db_session, hours=24)

        # Should include recent tasks but not old task
        recent_prompts = [task.prompt for task in recent_tasks]
        assert "Old task" not in recent_prompts
        assert "Recent task 1" in recent_prompts
        assert "Recent task 2" in recent_prompts
        assert "Very recent task" in recent_prompts

        # Should be ordered by created_at descending
        assert len(recent_tasks) >= 3
        for i in range(len(recent_tasks) - 1):
            assert recent_tasks[i].created_at >= recent_tasks[i+1].created_at

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_average_processing_time(self, test_db_session: AsyncSession, task_factory: TaskFactory):
        """Test getting average processing time for completed tasks."""
        now = datetime.utcnow()

        # Create completed tasks with different processing times
        fast_task = task_factory(
            prompt="Fast task",
            status=TaskStatus.COMPLETED,
            created_at=now - timedelta(seconds=10),
            updated_at=now - timedelta(seconds=5)  # 5 seconds processing
        )

        slow_task = task_factory(
            prompt="Slow task",
            status=TaskStatus.COMPLETED,
            created_at=now - timedelta(minutes=2),
            updated_at=now - timedelta(minutes=1)  # 60 seconds processing
        )

        # Create a non-completed task (shouldn't be included)
        pending_task = task_factory(
            prompt="Pending task",
            status=TaskStatus.PENDING
        )

        await test_db_session.commit()

        avg_time = await task_crud.get_average_processing_time(test_db_session)

        # Should calculate average of completed tasks only
        # (5 + 60) / 2 = 32.5 seconds
        assert avg_time > 0
        # Allow some tolerance for database timestamp precision
        assert 30 < avg_time < 35


class TestDatabaseTransactions:
    """Test database transaction handling."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_commit(self, test_db_session: AsyncSession):
        """Test successful transaction commit."""
        task = Task(
            prompt="Transaction test",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task)
        await test_db_session.commit()

        # Verify task is accessible after commit
        result = await test_db_session.execute(
            select(Task).filter(Task.id == task.id)
        )
        retrieved_task = result.scalar_one_or_none()

        assert retrieved_task is not None
        assert retrieved_task.prompt == "Transaction test"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, test_db_session: AsyncSession):
        """Test transaction rollback on error."""
        # Create a task
        task1 = Task(
            prompt="Task before error",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )
        test_db_session.add(task1)

        # Try to create an invalid task (this will cause an error on commit)
        task2 = Task(
            prompt=None,  # This should cause an integrity error
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )
        test_db_session.add(task2)

        # Commit should fail
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            await test_db_session.commit()

        # Rollback the transaction
        await test_db_session.rollback()

        # Verify neither task was committed
        result = await test_db_session.execute(select(Task))
        tasks = result.scalars().all()

        # Should be empty since both tasks were in the failed transaction
        if len(tasks) > 0:
            # If there are other tasks, make sure they're not our test tasks
            prompts = [task.prompt for task in tasks]
            assert "Task before error" not in prompts

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_transactions(self, test_db_session: AsyncSession):
        """Test concurrent database transactions."""
        async with AsyncSessionLocal() as session1:
            async with AsyncSessionLocal() as session2:
                # Create task in session1
                task1 = Task(
                    prompt="Concurrent task 1",
                    model="gpt-3.5-turbo",
                    provider="openai",
                    priority=1,
                    status=TaskStatus.PENDING
                )
                session1.add(task1)
                await session1.commit()

                # Create task in session2
                task2 = Task(
                    prompt="Concurrent task 2",
                    model="deepseek-chat",
                    provider="deepseek",
                    priority=2,
                    status=TaskStatus.PENDING
                )
                session2.add(task2)
                await session2.commit()

                # Verify both tasks exist
                result1 = await session1.execute(select(Task).filter(Task.id == task1.id))
                retrieved_task1 = result1.scalar_one_or_none()
                assert retrieved_task1 is not None
                assert retrieved_task1.prompt == "Concurrent task 1"

                result2 = await session2.execute(select(Task).filter(Task.id == task2.id))
                retrieved_task2 = result2.scalar_one_or_none()
                assert retrieved_task2 is not None
                assert retrieved_task2.prompt == "Concurrent task 2"


class TestSynchronousCRUD:
    """Test synchronous CRUD functions used by Celery tasks."""

    @pytest.mark.integration
    def test_update_task_status_sync_success(self):
        """Test synchronous task status update for Celery."""
        from app.database import get_sync_db_session
        from app.crud.task import update_task_status_sync

        with get_sync_db_session() as db:
            # Create task
            task = Task(
                prompt="Sync status test",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            task_id = task.id

        # Update status synchronously
        success = update_task_status_sync(db, str(task_id), TaskStatus.COMPLETED)
        assert success is True

        # Verify update
        with get_sync_db_session() as db:
            updated_task = db.query(Task).filter(Task.id == task_id).first()
            assert updated_task is not None
            assert updated_task.status == TaskStatus.COMPLETED

    @pytest.mark.integration
    def test_update_task_status_sync_not_found(self):
        """Test synchronous status update for non-existent task."""
        from app.database import get_sync_db_session
        from app.crud.task import update_task_status_sync

        with get_sync_db_session() as db:
            success = update_task_status_sync(db, "99999", TaskStatus.COMPLETED)
            assert success is False

    @pytest.mark.integration
    def test_update_task_result_sync_success(self):
        """Test synchronous task result update for Celery."""
        from app.database import get_sync_db_session
        from app.crud.task import update_task_result_sync

        with get_sync_db_session() as db:
            # Create task
            task = Task(
                prompt="Sync result test",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            task_id = task.id

        # Update result synchronously
        result_text = "This is a test result from Celery"
        success = update_task_result_sync(db, str(task_id), TaskStatus.COMPLETED, result_text)
        assert success is True

        # Verify update
        with get_sync_db_session() as db:
            updated_task = db.query(Task).filter(Task.id == task_id).first()
            assert updated_task is not None
            assert updated_task.status == TaskStatus.COMPLETED
            assert updated_task.result == result_text

    @pytest.mark.integration
    def test_get_task_sync_success(self):
        """Test synchronous task retrieval for Celery."""
        from app.database import get_sync_db_session
        from app.crud.task import get_task_sync

        with get_sync_db_session() as db:
            # Create task
            task = Task(
                prompt="Sync get test",
                model="gpt-3.5-turbo",
                provider="openai",
                priority=1,
                status=TaskStatus.PENDING
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            task_id = task.id

        # Get task synchronously
        with get_sync_db_session() as db:
            retrieved_task = get_task_sync(db, str(task_id))

        assert retrieved_task is not None
        assert retrieved_task.id == task_id
        assert retrieved_task.prompt == "Sync get test"

    @pytest.mark.integration
    def test_get_task_sync_not_found(self):
        """Test synchronous retrieval of non-existent task."""
        from app.database import get_sync_db_session
        from app.crud.task import get_task_sync

        with get_sync_db_session() as db:
            retrieved_task = get_task_sync(db, "99999")
            assert retrieved_task is None


class TestDatabaseConstraints:
    """Test database constraints and data integrity."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unique_primary_key(self, test_db_session: AsyncSession):
        """Test that primary key uniqueness is enforced."""
        # Create first task
        task1 = Task(
            prompt="First task",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )
        test_db_session.add(task1)
        await test_db_session.commit()

        # Try to manually set same ID on second task (should fail)
        task2 = Task(
            id=task1.id,  # Try to use same ID
            prompt="Second task",
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task2)

        with pytest.raises(Exception):  # Could be IntegrityError or similar
            await test_db_session.commit()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_null_constraints(self, test_db_session: AsyncSession):
        """Test that NOT NULL constraints are enforced."""
        # This should fail because prompt is required
        task = Task(
            prompt=None,  # Required field
            model="gpt-3.5-turbo",
            provider="openai",
            priority=1,
            status=TaskStatus.PENDING
        )

        test_db_session.add(task)

        with pytest.raises(Exception):  # Should be IntegrityError
            await test_db_session.commit()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self):
        """Test foreign key constraints (if any)."""
        # This test would be relevant if we had foreign key relationships
        # For now, it's a placeholder for future extensions
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])