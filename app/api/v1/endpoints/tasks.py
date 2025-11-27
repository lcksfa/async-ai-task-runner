from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas import TaskCreate, TaskResponse
from app.database import get_db
from app.crud import task as task_crud
from app.worker.tasks.ai_tasks import run_ai_text_generation

router = APIRouter()


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Create a new task")
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new AI processing task.

    - **prompt**: The AI prompt to process (required, 1-1000 characters)
    - **model**: The AI model to use (default: gpt-3.5-turbo)
    - **priority**: Task priority from 1-10 (default: 1)

    Returns the created task with assigned ID and timestamps.

    The task will be processed asynchronously in the background.
    """
    try:
        # 1. Create task record in database
        task = await task_crud.create_task(db=db, obj_in=task_in)

        # 2. Trigger Celery task for AI processing
        try:
            # Convert task.id to string for Celery compatibility
            run_ai_text_generation.delay(
                task_id=str(task.id),
                prompt=task.prompt,
                model=task.model,
                provider=task.provider
            )
            print(f"🚀 Celery task triggered for task_id: {task.id}")
            print(f"🔌 Provider: {task.provider or 'default'}")
            print(f"🧠 Model: {task.model or 'default'}")
        except Exception as celery_error:
            print(f"⚠️ Failed to trigger Celery task: {celery_error}")
            # Continue without Celery - task will remain in PENDING state

        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/tasks", response_model=List[TaskResponse], summary="Get all tasks")
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of tasks with pagination.

    - **skip**: Number of tasks to skip (default: 0)
    - **limit**: Maximum number of tasks to return (default: 100)
    """
    try:
        tasks = await task_crud.get_tasks(db=db, skip=skip, limit=limit)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tasks: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get a specific task")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific task by ID.
    """
    task = await task_crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return task