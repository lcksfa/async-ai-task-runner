from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from typing import List, Optional
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.schemas import TaskStatus


async def create_task(db: AsyncSession, *, obj_in: TaskCreate) -> Task:
    """Create a new task"""
    db_obj = Task(
        prompt=obj_in.prompt,
        model=obj_in.model,
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
def update_task_status_sync(db: Session, task_id: str, status: TaskStatus) -> bool:
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
    except Exception as e:
        db.rollback()
        print(f"Error updating task status: {e}")
        return False


def update_task_result_sync(db: Session, task_id: str, status: TaskStatus, result: str = None) -> bool:
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
    except Exception as e:
        db.rollback()
        print(f"Error updating task result: {e}")
        return False


def get_task_sync(db: Session, task_id: str) -> Optional[Task]:
    """Get a task by ID (synchronous version for Celery)"""
    try:
        # Try to convert string ID to integer for database query
        try:
            int_id = int(task_id)
            return db.query(Task).filter(Task.id == int_id).first()
        except ValueError:
            return db.query(Task).filter(Task.id == task_id).first()
    except Exception as e:
        print(f"Error getting task: {e}")
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