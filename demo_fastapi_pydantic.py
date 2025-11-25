#!/usr/bin/env python3
"""
FastAPI 与 Pydantic 实战演示

这个脚本演示了 FastAPI 和 Pydantic 的核心概念，包括：
1. 数据验证和序列化
2. 依赖注入
3. 错误处理
4. 自动文档生成

运行方式:
    uv run python demo_fastapi_pydantic.py

然后在浏览器中访问 http://localhost:8002/docs
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import asyncio
import random

# ====== 1. Pydantic 模型定义 ======

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskPriority(int, Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    URGENT = 10

class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., min_length=1, max_length=100, description="任务标题")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任务优先级")
    tags: List[str] = Field(default_factory=list, description="任务标签")

    @field_validator('title')
    @classmethod
    def title_must_contain_alpha(cls, v):
        """自定义验证器：标题必须包含字母"""
        if not any(c.isalpha() for c in v):
            raise ValueError('标题必须包含至少一个字母')
        return v

    @field_validator('tags')
    @classmethod
    def tags_must_be_unique(cls, v):
        """自定义验证器：标签必须唯一"""
        if len(v) != len(set(v)):
            raise ValueError('标签不能重复')
        return v

class TaskCreate(TaskBase):
    """创建任务的模型"""
    # 继承 TaskBase 的所有字段
    pass

class TaskUpdate(BaseModel):
    """更新任务的模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    tags: Optional[List[str]] = None

class TaskResponse(TaskBase):
    """响应任务模型"""
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processing_time: Optional[float] = None  # 处理时间（秒）

class User(BaseModel):
    """用户模型"""
    name: str
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    website: Optional[HttpUrl] = None  # 自动验证URL格式

class TaskStatistics(BaseModel):
    """任务统计模型"""
    total_tasks: int
    pending_tasks: int
    processing_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_processing_time: Optional[float] = None

# ====== 2. 内存数据存储（演示用） ======

class MemoryStorage:
    """内存存储类（模拟数据库）"""

    def __init__(self):
        self.tasks = {}
        self.next_id = 1
        self.users = {}

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """创建任务"""
        task_id = self.next_id
        self.next_id += 1

        now = datetime.now()

        task = TaskResponse(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            tags=task_data.tags,
            status=TaskStatus.PENDING,
            created_at=now,
            result=None
        )

        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: int) -> Optional[TaskResponse]:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_tasks(self, skip: int = 0, limit: int = 10, status: Optional[TaskStatus] = None) -> List[TaskResponse]:
        """获取任务列表"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [task for task in tasks if task.status == status]

        # 按创建时间排序
        tasks.sort(key=lambda x: x.created_at, reverse=True)

        return tasks[skip:skip + limit]

    def update_task(self, task_id: int, task_update: TaskUpdate) -> Optional[TaskResponse]:
        """更新任务"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        update_data = task_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.now()
        return task

    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def process_task(self, task_id: int) -> Optional[TaskResponse]:
        """模拟处理任务"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        # 更新状态为处理中
        task.status = TaskStatus.PROCESSING
        task.updated_at = datetime.now()

        return task

    def complete_task(self, task_id: int, result: Dict[str, Any]) -> Optional[TaskResponse]:
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        task.status = TaskStatus.COMPLETED
        task.result = result
        task.updated_at = datetime.now()

        # 计算处理时间
        if task.created_at:
            processing_time = (task.updated_at - task.created_at).total_seconds()
            task.processing_time = round(processing_time, 2)

        return task

    def get_statistics(self) -> TaskStatistics:
        """获取任务统计"""
        tasks = list(self.tasks.values())

        stats = TaskStatistics(
            total_tasks=len(tasks),
            pending_tasks=len([t for t in tasks if t.status == TaskStatus.PENDING]),
            processing_tasks=len([t for t in tasks if t.status == TaskStatus.PROCESSING]),
            completed_tasks=len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            failed_tasks=len([t for t in tasks if t.status == TaskStatus.FAILED])
        )

        # 计算平均处理时间
        completed_tasks = [t for t in tasks if t.processing_time is not None]
        if completed_tasks:
            avg_time = sum(t.processing_time for t in completed_tasks) / len(completed_tasks)
            stats.average_processing_time = round(avg_time, 2)

        return stats

# ====== 3. 依赖注入函数 ======

async def get_storage() -> MemoryStorage:
    """获取存储实例的依赖"""
    # 在实际应用中，这里可能是数据库连接
    return MemoryStorage()

async def validate_task_exists(
    task_id: int,
    storage: MemoryStorage = Depends(get_storage)
) -> TaskResponse:
    """验证任务是否存在的依赖"""
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    return task

def common_parameters(
    skip: int = Query(0, ge=0, description="跳过的任务数量"),
    limit: int = Query(10, ge=1, le=100, description="返回的任务数量限制"),
    status: Optional[TaskStatus] = Query(None, description="按状态过滤")
):
    """通用查询参数依赖"""
    return {"skip": skip, "limit": limit, "status": status}

# ====== 4. FastAPI 应用创建 ======

app = FastAPI(
    title="FastAPI Pydantic Demo",
    description="演示 FastAPI 和 Pydantic 核心概念的示例应用",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== 5. API 路由定义 ======

@app.get("/", tags=["Root"])
async def root():
    """根端点"""
    return {
        "message": "FastAPI Pydantic Demo",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.0.0"
    }

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
async def create_task(
    task: TaskCreate,
    storage: MemoryStorage = Depends(get_storage)
):
    """
    创建新任务

    - **title**: 任务标题（必填，1-100字符，必须包含字母）
    - **description**: 任务描述（可选，最多1000字符）
    - **priority**: 任务优先级（默认为MEDIUM）
    - **tags**: 任务标签列表（可选，必须唯一）
    """
    return storage.create_task(task)

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def get_tasks(
    params: dict = Depends(common_parameters),
    storage: MemoryStorage = Depends(get_storage)
):
    """
    获取任务列表

    支持分页和状态过滤
    """
    return storage.get_tasks(**params)

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task: TaskResponse = Depends(validate_task_exists)
):
    """
    获取单个任务

    自动验证任务是否存在，不存在时返回404错误
    """
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(
    task_update: TaskUpdate,
    task: TaskResponse = Depends(validate_task_exists),
    storage: MemoryStorage = Depends(get_storage)
):
    """
    更新任务

    只更新提供的字段，未提供的字段保持不变
    """
    return storage.update_task(task.id, task_update)

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
async def delete_task(
    task: TaskResponse = Depends(validate_task_exists),
    storage: MemoryStorage = Depends(get_storage)
):
    """
    删除任务

    任务不存在时返回404，成功时返回204
    """
    storage.delete_task(task.id)
    return None

@app.post("/tasks/{task_id}/process", response_model=TaskResponse, tags=["Tasks"])
async def process_task(
    task: TaskResponse = Depends(validate_task_exists),
    storage: MemoryStorage = Depends(get_storage)
):
    """
    开始处理任务

    模拟异步处理过程
    """
    return storage.process_task(task.id)

@app.post("/tasks/{task_id}/complete", response_model=TaskResponse, tags=["Tasks"])
async def complete_task(
    result_data: Dict[str, Any],
    task: TaskResponse = Depends(validate_task_exists),
    storage: MemoryStorage = Depends(get_storage)
):
    """
    完成任务

    需要提供处理结果数据
    """
    return storage.complete_task(task.id, result_data)

@app.get("/statistics", response_model=TaskStatistics, tags=["Statistics"])
async def get_statistics(
    storage: MemoryStorage = Depends(get_storage)
):
    """
    获取任务统计信息

    包括各种状态的任务数量和平均处理时间
    """
    return storage.get_statistics()

# ====== 6. 错误处理示例 ======

@app.post("/users", tags=["Users"])
async def create_user(user: User):
    """
    创建用户示例

    演示复杂的数据验证，包括邮箱格式和URL验证
    """
    # 模拟用户存储
    return {"message": f"User {user.name} created successfully", "user": user}

# ====== 7. 数据验证错误演示 ======

@app.post("/validation-demo", tags=["Demo"])
async def validation_demo(
    data: dict
):
    """
    数据验证演示端点

    发送各种数据来测试验证规则
    """
    # 这个端点主要用于演示验证错误
    return {"received": data}

# ====== 8. 启动信息 ======

@app.get("/startup-info", tags=["System"])
async def startup_info():
    """启动信息（替代startup事件）"""
    return {
        "message": "🚀 FastAPI Pydantic Demo 运行中!",
        "docs": "http://localhost:8002/docs",
        "redoc": "http://localhost:8002/redoc",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn

    # 启动应用
    uvicorn.run(
        "demo_fastapi_pydantic:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )