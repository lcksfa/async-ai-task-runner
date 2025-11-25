from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskBase(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="The AI prompt to process")
    model: str = Field(default="gpt-3.5-turbo", description="The AI model to use")
    priority: int = Field(default=1, ge=1, le=10, description="Task priority (1-10)")


class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    prompt: Optional[str] = Field(None, min_length=1, max_length=1000)
    model: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[TaskStatus] = None


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: int
    status: TaskStatus
    result: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    app_name: str
    version: str
    timestamp: datetime