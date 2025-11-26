# 配置基本 Celery 实例详细指南

## 📋 概述

本指南详细解释如何在 Async AI Task Runner 项目中配置基本的 Celery 实例，从零开始到生产就绪的完整配置过程。

## 🎯 学习目标

- 理解 Celery 基本概念和架构
- 掌握 Celery 实例的创建和配置
- 学会任务定义和调用方法
- 掌握 Worker 启动和监控
- 了解高级配置选项

---

## 🏗️ Celery 基础概念

### 核心组件架构

```
┌─────────────────┐    消息     ┌─────────────────┐    任务    ┌─────────────────┐
│   Producer    │  ◀──────▶   │    Broker   │  ◀──────▶   │   Consumer  │
│  (生产者)    │           │  (消息队列)  │           │  (消费者)  │
└─────────────────┘           └─────────────────┘           └─────────┘
       ↓                           ↓                           ↓
  应用程序                      Redis                       Worker
  FastAPI                      任务队列                      Celery
```

### 关键术语解释

| 术语 | 说明 | 在我们项目中的实现 |
|------|------|-------------------|
| **Task** | 要执行的工作单元 | `run_ai_text_generation()` |
| **Worker** | 执行任务的进程 | `celery -A app.worker worker` |
| **Broker** | 消息中间件，存储待处理任务 | `redis://localhost:6379/1` |
| **Backend** | 存储任务结果的地方 | `redis://localhost:6379/2` |
| **Queue** | 任务队列，按优先级分类 | `ai_processing`, `demo_tasks` |

---

## 🔧 环境准备

### 1. 依赖安装

**文件**: [`pyproject.toml`](pyproject.toml:19-21)

```toml
dependencies = [
    # ... 其他依赖
    "celery[redis]>=5.3.0",    # Celery 核心和 Redis 支持
    "redis>=5.0.0",            # Redis Python 客户端
    "flower>=2.0.0",           # Celery 监控工具
]
```

**安装命令**:
```bash
# 使用 uv（我们的项目推荐）
uv sync

# 或者使用 pip
pip install "celery[redis]>=5.3.0" "redis>=5.0.0" "flower>=2.0.0"
```

### 2. Redis 服务启动

```bash
# 使用 Docker 启动 Redis（推荐）
docker run -d --name redis-ai-task -p 6379:6379 redis:7-alpine

# 验证 Redis 连接
docker exec redis-ai-task redis-cli ping
# 应该返回: PONG

# 或者使用系统安装的 Redis
redis-server --daemonize yes
redis-cli ping
```

### 3. PostgreSQL 数据库（可选）

```bash
# 启动 PostgreSQL
docker run -d --name async-ai-postgres -p 5433:5432 \
  -e POSTGRES_DB=task_runner \
  -e POSTGRES_USER=taskuser \
  -e POSTGRES_PASSWORD=taskpass \
  postgres:16
```

---

## 🎯 第一步：创建基本 Celery 应用

### 1.1 最小化配置示例

```python
# minimal_celery_app.py
from celery import Celery

# 最简单的 Celery 应用
app = Celery(
    'myapp',                    # 应用名称
    broker='redis://localhost:6379/0',  # Redis 消息代理
    backend='redis://localhost:6379/0'   # 结果存储
)

@app.task
def add(x, y):
    """最简单的任务定义"""
    return x + y
```

### 1.2 我们项目的配置实现

**文件**: [`app/worker/app.py`](app/worker/app.py)

```python
from celery import Celery
from app.core.config import settings

# 🎯 创建 Celery 应用实例
celery_app = Celery(
    "async_ai_task_runner",              # 应用名称
    broker=settings.celery_broker_url,  # 消息代理地址
    backend=settings.celery_result_backend,  # 结果存储地址
    include=[                           # 包含的任务模块
        "app.worker.tasks.ai_tasks",
        "app.worker.tasks.demo_tasks"
    ]
)

# ⚙️ 高级配置（稍后详细解释）
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

### 1.3 环境变量配置

**文件**: [`app/core/config.py`](app/core/config.py:13-16)

```python
class Settings(BaseSettings):
    # Redis & Celery 配置
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"      # 📤 任务队列
    celery_result_backend: str = "redis://localhost:6379/2"  # 💾 结果存储

    class Config:
        env_file = ".env"
        case_sensitive = False
```

**为什么使用不同的Redis数据库？**
- `redis://localhost:6379/1` - 存储任务队列（Broker）
- `redis://localhost:6379/2` - 存储任务结果（Backend）
- **好处**: 数据分离，便于管理和清理

---

## ⚙️ 第二步：高级配置详解

### 2.1 序列化配置

```python
# 在 app/worker/app.py 中
celery_app.conf.update(
    # 🔄 序列化配置
    task_serializer="json",           # 任务数据如何序列化
    accept_content=["json"],          # Worker接受的内容类型
    result_serializer="json",         # 结果数据如何序列化

    # ⏰ 时间配置
    timezone="UTC",                   # 使用UTC时间
    enable_utc=True,                  # 启用UTC时间
)
```

**为什么要用JSON序列化？**
- ✅ **可读性好**: 人类可读的数据格式
- ✅ **轻量级**: 比pickle序列化更轻量
- ✅ **跨语言**: 支持多种编程语言
- ✅ **安全性**: 避免pickle的安全风险

### 2.2 任务路由配置

```python
# 在 app/worker/app.py 中
celery_app.conf.update(
    # 🎯 任务路由配置 - 按功能分离任务
    task_routes={
        "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.worker.tasks.demo_tasks.*": {"queue": "demo_tasks"},
        "app.worker.tasks.urgent.*": {"queue": "urgent"},
    }
)
```

**路由优势**：
- ✅ **负载分离**: 不同类型任务由不同的Worker处理
- ✅ **性能优化**: 可以为不同队列配置不同的Worker
- ✅ **故障隔离**: 一个队列的问题不影响其他队列

**启动特定队列的Worker**:
```bash
# 只处理AI任务的Worker
celery -A app.worker worker --queues=ai_processing

# 只处理紧急任务的Worker
celery -A app.worker worker --queues=urgent

# 处理所有任务的Worker
celery -A app.worker worker --queues=ai_processing,demo_tasks,urgent
```

### 2.3 性能配置

```python
# 在 app/worker/app.py 中
celery_app.conf.update(
    # 🚀 Worker性能配置
    worker_prefetch_multiplier=1,    # Worker预取任务数（重要！）
    task_acks_late=True,           # 任务完成后再确认（可靠性）

    # 📊 结果和监控配置
    result_expires=3600,            # 结果过期时间（1小时）
    worker_send_task_events=True,   # 启用任务事件追踪

    # 🛡️ 可靠性配置
    worker_disable_rate_limits=False,  # 禁用速率限制
    task_reject_on_worker_lost=True, # Worker丢失时拒绝任务
)
```

**重要配置说明**：

#### `worker_prefetch_multiplier=1`
```python
# 值为1（推荐）：
# Worker一次只预取1个任务，完成任务后再取下一个
# 防止Worker过载，确保任务按顺序处理

# 值>1（谨慎使用）：
# Worker可以预取多个任务
# 适合快速小任务，但可能导致任务堆积
```

#### `task_acks_late=True`
```python
# True（推荐）：
# 任务成功完成后才发送ACK确认
# 如果Worker崩溃，任务会被重新分配给其他Worker
# 确保任务不丢失

# False（默认）：
# Worker接收到任务后立即发送ACK确认
# 如果Worker崩溃，任务会丢失
# 性能更好，但可靠性较低
```

### 2.4 监控配置

```python
# 在 app/worker/app.py 中
celery_app.conf.update(
    # 📊 启用监控功能
    worker_send_task_events=True,   # 发送任务生命周期事件
    task_send_sent_event=True,      # 发送任务发送事件

    # 📈 性能监控
    task_track_started=True,        # 跟踪任务开始时间
    task_track_completed=True,      # 跟踪任务完成时间
)
```

---

## 📝 第三步：定义任务

### 3.1 基础任务定义

**文件**: [`app/worker/tasks/demo_tasks.py`](app/worker/tasks/demo_tasks.py:11-25)

```python
from app.worker.app import celery_app
import time

@celery_app.task(name="simple_calculation")  # 明确任务名称（推荐）
def simple_calculation(a: int, b: int, operation: str = "add"):
    """
    简单的数学计算任务
    用于测试 Celery 基本功能
    """
    print(f"🔢 开始计算: {a} {operation} {b}")

    # 模拟计算时间
    time.sleep(2)

    if operation == "add":
        result = a + b
    elif operation == "multiply":
        result = a * b
    elif operation == "subtract":
        result = a - b
    else:
        raise ValueError(f"不支持的操作: {operation}")

    print(f"✅ 计算结果: {result}")

    return {
        "operation": f"{a} {operation} {b}",
        "result": result,
        "timestamp": time.time()
    }
```

### 3.2 高级任务特性

#### 3.2.1 带进度跟踪的任务

**文件**: [`app/worker/tasks/ai_tasks.py`](app/worker/tasks/ai_tasks.py:12-15)

```python
from app.worker.app import celery_app
from app.models import TaskStatus
from app.crud.task import update_task_status, update_task_result

@celery_app.task(bind=True, name="run_ai_text_generation")  # bind=True
def run_ai_text_generation(self, task_id: str, prompt: str, model: str = "gpt-3.3.5-turbo"):
    """
    🎯 AI文本生成任务
    特性：
    1. bind=True - 绑定任务实例，支持进度跟踪
    2. 数据库状态同步 - 实时更新任务状态
    3. 错误重试机制 - 自动失败恢复
    """
```

**`bind=True` 的作用**：
```python
# self 包含任务实例信息
print(f"Task ID: {self.request.id}")           # 任务唯一ID
print(f"Task name: {self.name}")           # 任务名称
print(f"Retry count: {self.request.retries}") # 重试次数

# 🔑 实时进度更新
self.update_state(
    state='PROGRESS',
    meta={
        'progress': 50,
        'status': '处理中... 50%'
    }
)
```

#### 3.2.2 带重试机制的任务

```python
@celery_app.task(bind=True, max_retries=3)  # 最大重试3次
def robust_task(self, data):
    """
    带重试机制的健壮任务
    """
    try:
        # 可能失败的操作
        result = risky_operation(data)
        return result
    except ConnectionError as exc:
        # 网络错误 - 重试
        print(f"🔄 网络错误，60秒后重试")
        raise self.retry(exc=exc, countdown=60)  # 60秒后重试
    except ValueError as exc:
        # 数据错误 - 不重试，直接失败
        print(f"❌ 数据错误: {exc}")
        raise exc
    except Exception as exc:
        # 其他错误 - 重试
        print(f"🔄 未知错误，120秒后重试")
        raise self.retry(exc=exc, countdown=120)  # 120秒后重试
```

#### 3.2.3 定时任务（可选）

```python
from celery.schedules import crontab

# 配置定时任务
celery_app.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'app.worker.tasks.maintenance.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
    'hourly-report': {
        'task': 'app.worker.tasks.reports.generate_hourly_stats',
        'schedule': crontab(minute=0),         # 每小时
    },
}

# 启动定时任务调度器
# celery -A app.worker beat --loglevel=info
```

---

## 🚀 第四步：运行和监控

### 4.1 启动 Worker

#### 基础启动
```bash
# 最简单的启动方式
celery -A app.worker worker --loglevel=info
```

#### 生产环境启动
```bash
# 推荐的生产环境配置
celery -A app.worker worker \
    --loglevel=info \
    --concurrency=4 \           # 4个并发进程
    --prefetch-multiplier=1 \   # 防止过载
    --max-tasks-per-child=1000 # 每1000个任务后重启
```

#### 队列专用启动
```bash
# 只处理AI任务的Worker
celery -A app.worker worker --queues=ai_processing --concurrency=2

# 启动多个Worker进程
celery -A app.worker worker --concurrency=2 &
celery -A app.worker worker --concurrency=2 &
```

### 4.2 启动监控工具

#### Flower 监控面板
```bash
# 启动Flower
celery -A app.worker flower --port=5555

# 访问监控界面
# http://localhost:5555
```

**Flower功能**：
- 📊 **实时统计**: 任务执行数量、成功率
- 👥 **Worker状态**: 在线Worker列表和状态
- 📈 **任务历史**: 任务执行记录和时间分析
- 🔧 **任务管理**: 手动重试、撤销任务

#### 命令行监控
```bash
# 查看活跃任务
celery -A app.worker inspect active

# 查看注册的任务
celery -A app.worker inspect registered

# 查看Worker统计
celery -A app.worker inspect stats

# 查看队列长度
docker exec redis-ai-task redis-cli llen celery
```

### 4.3 验证配置

#### 检查配置
```bash
# 查看应用配置
celery -A app.worker inspect conf

# 输出示例：
# {
#   'task_serializer': 'json',
#   'accept_content': ['json'],
#   'result_serializer': 'json',
#   'timezone': 'UTC',
#   'task_routes': {...}
# }
```

#### 测试任务
```bash
# 测试基本任务
python -c "
from app.worker.tasks.demo_tasks import simple_calculation

# 发送任务
result = simple_calculation.delay(10, 20, 'add')
print(f'任务ID: {result.id}')

# 等待结果
print(f'结果: {result.get(timeout=10)}')
"
```

**预期输出**：
```
任务ID: abc-123-def-456-ghi
结果: {'operation': '10 add 20', 'result': 30, 'timestamp': 1634567890.123}
```

---

## 🔍 第五步：集成FastAPI

### 5.1 FastAPI 集成

**文件**: [`app/api/v1/endpoints/tasks.py`](app/api/v1/endpoints/tasks.py:12-49)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.worker.tasks.ai_tasks import run_ai_text_generation
from app.crud import task as task_crud

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    异步任务创建流程：
    1. 创建数据库记录（立即）
    2. 触发Celery任务（异步）
    3. 立即返回响应（快速）
    """
    try:
        # 1. 创建任务记录在数据库
        task = await task_crud.create_task(db=db, obj_in=task_in)

        # 2. 触发Celery任务进行异步处理
        try:
            # 🔑 类型转换：int → str
            run_ai_text_generation.delay(
                task_id=str(task.id),
                prompt=task.prompt,
                model=task.model or "gpt-3.5-turbo"
            )
            print(f"🚀 Celery task triggered for task_id: {task.id}")
        except Exception as celery_error:
            # 🛡️ 容错处理 - Celery失败不影响API响应
            print(f"⚠️ Failed to trigger Celery task: {celery_error}")

        # 3. 立即返回任务ID
        return task

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )
```

### 5.2 工作流程分析

```
用户请求 → FastAPI
    ↓
1. 接收HTTP请求
2. 验证请求数据（Pydantic）
3. 创建数据库记录
    ↓
立即响应 ← 用户得到Task ID
    ↓
触发Celery任务 → Redis队列
    ↓
Celery Worker ← 从Redis获取任务
    ↓
开始处理任务 → 更新状态为PROCESSING
    ↓
完成处理 → 更新状态为COMPLETED
    ↓
数据库 ← 结果存储
```

### 5.3 API 响应时间对比

| 场景 | 同步处理 | 异步处理 | 性能提升 |
|------|----------|----------|----------|
| **用户提交任务** | 等待10-30秒 | <100毫秒 | **300倍** |
| **并发用户数** | 受连接数限制 | 理论无限制 | **线性扩展** |
| **系统稳定性** | 容易超时崩溃 | 高稳定性 | **质的飞跃** |

---

## 🛠️ 第六步：错误处理和可靠性

### 6.1 任务错误处理

```python
@celery_app.task(bind=True, max_retries=3)
def robust_task(self, data):
    try:
        # 业务逻辑
        result = process_data(data)
        return result
    except ConnectionError as exc:
        # 网络错误 - 可重试
        raise self.retry(exc=exc, countdown=60)
    except ValueError as exc:
        # 数据错误 - 不重试
        raise exc
    except Exception as exc:
        # 未知错误 - 重试
        raise self.retry(exc=exc, countdown=60)
```

### 6.2 数据库事务安全

**文件**: [`app/database.py`](app/database.py:46-57)

```python
@contextlib.contextmanager
def get_sync_db_session():
    """同步数据库会话 - 确保连接正确关闭"""
    session = SyncSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()  # 🔒 异常时回滚
        raise
    finally:
        session.close()   # 🔒 确保连接关闭
```

**使用方式**：
```python
# ✅ 正确的数据库使用方式
@celery_app.task
def db_task():
    with get_sync_db_session() as db:
        result = db.query(Task).all()
    return result

# ❌ 错误的使用方式（不能在Celery中使用async）
@celery.app.task
async def bad_db_task():
    async with get_db() as db:  # ❌ 不能在Celery中使用async
        return await db.query(Task).all()
```

### 6.3 任务状态同步

**文件**: [`app/crud/task.py`](app/crud/task.py:116-131)

```python
def update_task_status(task_id, status: TaskStatus) -> bool:
    """更新任务状态"""
    from app.database import get_sync_db_session

    # 🔑 处理不同类型的task_id
    task_id_str = str(task_id) if isinstance(task_id, int) else task_id

    with get_sync_db_session() as db:
        return update_task_status_sync(db, task_id_str, status)
```

**类型转换处理**：
```python
def update_task_status_sync(db: Session, task_id: str, status: TaskStatus):
    try:
        # 🔑 字符串ID转整数ID用于数据库查询
        int_id = int(task_id)
        task = db.query(Task).filter(Task.id == int_id).first()
    except ValueError:
        # 容错：支持字符串ID
        task = db.query(Task).filter(Task.id == task_id).first()

    if task:
        task.status = status
        db.commit()
        return True
    return False
```

---

## 📊 第七步：监控和日志

### 7.1 日志配置

```python
import logging
from celery.utils.log import get_task_logger

# 获取任务日志记录器
logger = get_task_logger(__name__)

@celery_app.task
def logged_task(data):
    logger.info(f"开始处理任务: {data}")

    try:
        result = process_data(data)
        logger.info(f"任务完成: {result}")
        return result
    except Exception as exc:
        logger.error(f"任务失败: {exc}")
        raise
```

### 7.2 性能监控

```python
# 在任务中添加性能统计
@celery_app.task(bind=True)
def monitored_task(self, data):
    import time
    start_time = time.time()

    # 任务逻辑
    result = process_data(data)

    end_time = time.time()
    duration = end_time - start_time

    self.update_state(
        state='SUCCESS',
        meta={
            'duration': duration,
            'items_processed': len(data)
        }
    )

    return result
```

### 7.3 关键指标

| 指标 | 监控方法 | 健康阈值 |
|------|----------|----------|
| **任务延迟** | Flower面板 | <5秒 |
| **任务成功率** | 计算公式 | >95% |
| **Worker数量** | `inspect stats` | 匹配预期 |
| **队列长度** | Redis命令 | <100 |
| **内存使用** | 系统监控 | <80% |

---

## 🔧 高级配置选项

### 8.1 连接池配置

```python
# 在 app/worker/app.py 中
celery_app.conf.update(
    broker_pool_limit=10,              # 连接池大小
    broker_connection_timeout=30,      # 连接超时时间
    broker_transport_options={
        'visibility_timeout': 3600,     # 任务可见性超时
        'retry_policy': {
            'timeout': 5.0
        }
    }
)
```

### 8.2 定时任务配置

```python
# 每天2点清理过期任务
celery_app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'app.worker.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

### 8.3 Worker自动重启

```bash
# 每1000个任务后重启Worker（防止内存泄漏）
celery -A app.worker worker --max-tasks-per-child=1000

# 每10分钟重启Worker（定期重启）
# 使用supervisor等进程管理工具
```

### 8.4 安全配置

```python
# 启用任务事件追踪（安全建议）
celery_app.conf.update(
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_send_success_event=True,
)

# 禁用不安全的序列化格式
celery_app.conf.update(
    accept_content=["json"],  # 只接受JSON
    task_serializer="json",       # 只使用JSON序列化
)
```

---

## 🐛 常见问题和解决方案

### 问题1：任务不执行

**症状**: 任务提交后状态一直是 PENDING

**排查步骤**:
```bash
# 1. 检查Worker状态
celery -A app.worker inspect active

# 2. 检查任务是否注册
celery -A app.worker inspect registered | grep your_task_name

# 3. 查看队列长度
docker exec redis-ai-task redis-cli llen celery

# 4. 检查Worker日志
docker-compose logs worker
```

**解决方案**:
```bash
# 重启Worker
pkill -f "celery.*worker"
celery -A app.worker worker --loglevel=info
```

### 问题2：数据库连接错误

**症状**: Celery任务中数据库操作失败

**原因**: Celery任务不能使用异步数据库会话

**解决方案**:
```python
# ❌ 错误方式
@celery.task
async def bad_db_task():
    async with get_db() as db:  # ❌ 不能在Celery中使用async
        return await db.query(Task).all()

# ✅ 正确方式
@celery.task
def good_db_task():
    with get_sync_db_session() as db:  # ✅ 使用同步会话
        return db.query(Task).all()
```

### 问题3：内存泄漏

**症状**: Worker内存持续增长

**解决方案**:
```bash
# 限制每个Worker处理的任务数
celery -A app.worker worker --max-tasks-per-child=1000

# 定期重启Worker
# 使用supervisor等进程管理工具
```

### 问题4：任务重复执行

**症状**: 相同任务被多次执行

**解决方案**: 确保任务幂等性
```python
@celery.task
def idempotent_task(unique_id):
    # 检查是否已处理
    if is_processed(unique_id):
        return get_result(unique_id)

    # 处理任务
    result = process_task(unique_id)

    # 标记已处理
    mark_processed(unique_id, result)

    return result
```

---

## 📚 完整配置示例

### 基础配置

```python
# app/worker/basic_app.py
from celery import Celery

app = Celery(
    'myapp',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

### 生产配置

```python
# app/worker/app.py (我们的实现)
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "async_ai_task_runner",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.worker.tasks.ai_tasks",
        "app.worker.tasks.demo_tasks"
    ]
)

celery_app.conf.update(
    # 序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # 任务路由
    task_routes={
        "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.worker.tasks.demo_tasks.*": {"queue": "demo_tasks"},
    },

    # 性能配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # 监控配置
    result_expires=3600,
    worker_send_task_events=True,
    task_send_sent_event=True,

    # 可靠性配置
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
)
```

---

## 🎯 总结

### 配置要点回顾

1. **应用创建**：使用 `Celery()` 创建应用实例
2. **Broker配置**：配置Redis作为消息代理
3. **Backend配置**：配置结果存储位置
4. **任务定义**：使用 `@celery_app.task` 装饰器
5. **Worker启动**：使用命令行参数启动工作进程
6. **监控集成**：使用Flower进行实时监控

### 配置最佳实践

1. **🔑 使用明确的任务名称** - `@celery_app.task(name="my_task")`
2. **🎯 分离不同类型任务** - 使用任务路由和专用队列
3. **🛡️ 启用任务确认** - `task_acks_late=True`
4. **📊 完善监控配置** - 启用事件追踪
5. **⚡️ 设置合理的重试机制** - 避免无限重试

### 完整流程示例

```bash
# 1. 启动Redis
docker run -d --name redis-ai-task -p 6379:6379 redis:7-alpine

# 2. 启动Worker
celery -A app.worker worker --loglevel=info --concurrency=2

# 3. 启动Flower（可选）
celery -A app.worker flower --port=5555

# 4. 测试配置
python -c "
from app.worker.tasks.demo_tasks import simple_calculation
result = simple_calculation.delay(10, 20, 'add')
print(f'Task ID: {result.id}')
print(f'Result: {result.get(timeout=10)}')
"

# 5. 访问监控面板
# http://localhost:5555
```

这个配置指南涵盖了从基础到生产的完整Celery配置，您可以根据需要选择合适的配置级别！🎯