from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Union
import logging

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskStatus

logger = logging.getLogger(__name__)


async def create_task(db: AsyncSession, *, obj_in: TaskCreate) -> Task:
    """Create a new task"""
    db_obj = Task(
        prompt=obj_in.prompt,
        model=obj_in.model,
        provider=obj_in.provider,
        priority=obj_in.priority,
        status=TaskStatus.PENDING
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
    """Get a task by ID"""
    result = await db.execute(select(Task).filter(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Task]:
    """Get multiple tasks with pagination"""
    result = await db.execute(
        select(Task).offset(skip).limit(limit).order_by(Task.created_at.desc())
    )
    return result.scalars().all()


async def update_task(db: AsyncSession, *, db_obj: Task, obj_in: TaskUpdate) -> Task:
    """Update an existing task"""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_task(db: AsyncSession, *, task_id: int) -> bool:
    """Delete a task by ID"""
    result = await db.execute(delete(Task).filter(Task.id == task_id))
    await db.commit()
    return result.rowcount > 0


# 同步版本的CRUD函数，用于Celery任务
def update_task_status_sync(db: Session, task_id: Union[int, str], status: TaskStatus) -> bool:
    """Update task status (synchronous version for Celery)"""
    try:
        # Try to convert string ID to integer for database query
        try:
            int_id = int(task_id)
            task = db.query(Task).filter(Task.id == int_id).first()
        except ValueError:
            task = db.query(Task).filter(Task.id == task_id).first()

        if task:
            task.status = status
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating task status: {e}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating task status: {e}")
        return False


def update_task_result_sync(db: Session, task_id: Union[int, str], status: TaskStatus, result: str = None) -> bool:
    """Update task status and result (synchronous version for Celery)"""
    try:
        # Try to convert string ID to integer for database query
        try:
            int_id = int(task_id)
            task = db.query(Task).filter(Task.id == int_id).first()
        except ValueError:
            task = db.query(Task).filter(Task.id == task_id).first()

        if task:
            task.status = status
            if result:
                task.result = result
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating task result: {e}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating task result: {e}")
        return False


def get_task_sync(db: Session, task_id: Union[int, str]) -> Optional[Task]:
    """Get a task by ID (synchronous version for Celery)"""
    try:
        # Try to convert string ID to integer for database query
        try:
            int_id = int(task_id)
            return db.query(Task).filter(Task.id == int_id).first()
        except ValueError:
            return db.query(Task).filter(Task.id == task_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting task: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting task: {e}")
        return None


# 为了向后兼容，保留原来的函数名
def update_task_status(task_id, status: TaskStatus) -> bool:
    """Update task status using synchronous database session"""
    from app.database import get_sync_db_session
    # Handle both string and integer task IDs
    task_id_str = str(task_id) if isinstance(task_id, int) else task_id
    with get_sync_db_session() as db:
        return update_task_status_sync(db, task_id_str, status)


def update_task_result(task_id, status: TaskStatus, result: str = None) -> bool:
    """Update task result using synchronous database session"""
    from app.database import get_sync_db_session
    # Handle both string and integer task IDs
    task_id_str = str(task_id) if isinstance(task_id, int) else task_id
    with get_sync_db_session() as db:
        return update_task_result_sync(db, task_id_str, status, result)


# MCP-specific CRUD functions
async def get_tasks_with_filters(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    created_after: Optional[datetime] = None
) -> List[Task]:
    """Get tasks with advanced filtering for MCP"""
    query = select(Task)

    if status:
        query = query.filter(Task.status == TaskStatus(status.upper()))

    if created_after:
        query = query.filter(Task.created_at >= created_after)

    query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def get_total_task_count(db: AsyncSession) -> int:
    """Get total number of tasks"""
    result = await db.execute(select(Task).count())
    return result.scalar() or 0


async def get_task_counts_by_status(db: AsyncSession) -> List[Task]:
    """Get task count grouped by status"""
    from sqlalchemy import func

    result = await db.execute(
        select(
            Task.status,
            func.count(Task.id).label('count')
        ).group_by(Task.status)
    )

    status_counts = []
    for row in result:
        status_counts.append(Task(status=row.status, count=row.count))

    return status_counts


async def get_model_usage_stats(db: AsyncSession) -> dict:
    """Get usage statistics by AI model"""
    from sqlalchemy import func

    result = await db.execute(
        select(
            Task.model,
            func.count(Task.id).label('total_tasks'),
            func.sum(func.case((Task.status == 'COMPLETED', 1), else_=0)).label('completed_tasks')
        ).group_by(Task.model)
    )

    usage_stats = {}
    for row in result:
        usage_stats[row.model] = type('UsageStats', (), {
            'total_tasks': row.total_tasks,
            'completed_tasks': row.completed_tasks or 0
        })()

    return usage_stats


async def get_recent_tasks(db: AsyncSession, hours: int = 24, limit: int = 50) -> List[Task]:
    """Get recent tasks within specified hours"""
    from datetime import timedelta

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(Task)
        .filter(Task.created_at >= cutoff_time)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_average_processing_time(db: AsyncSession) -> float:
    """Get average processing time in seconds"""
    from sqlalchemy import func
    from datetime import datetime

    result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', Task.updated_at - Task.created_at)
            )
        ).filter(Task.status == 'COMPLETED')
    )

    avg_time = result.scalar()
    return float(avg_time) if avg_time else 0.0