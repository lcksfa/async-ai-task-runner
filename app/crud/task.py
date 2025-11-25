from sqlalchemy.ext.asyncio import AsyncSession
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