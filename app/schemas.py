from pydantic import BaseModel, Field, field_serializer
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

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """将UTC时间转换为本地时间字符串"""
        if value is None:
            return None
        # 转换为本地时间并格式化
        local_time = value.astimezone()
        return local_time.strftime("%Y-%m-%d %H:%M:%S")

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    app_name: str
    version: str
    timestamp: datetime