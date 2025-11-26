# Celery 新手完整教程

## 📚 目录

1. [Celery 简介](#1-celery-简介)
2. [核心概念](#2-核心概念)
3. [环境搭建](#3-环境搭建)
4. [基础配置](#4-基础配置)
5. [创建第一个任务](#5-创建第一个任务)
6. [运行和监控](#6-运行和监控)
7. [高级特性](#7-高级特性)
8. [错误处理](#8-错误处理)
9. [最佳实践](#9-最佳实践)
10. [常见问题](#10-常见问题)

---

## 1. Celery 简介

### 什么是 Celery？

Celery 是一个**分布式任务队列**，专注于**实时处理**和**任务调度**。它是 Python 生态系统中最重要的异步任务处理框架之一。

### 为什么需要 Celery？

想象这个场景：
```python
# 传统同步处理 - 用户体验差
@app.post("/generate-image")
def generate_image(prompt):
    # 图片生成需要 30 秒
    result = ai_service.generate_image(prompt)  # 阻塞 30 秒！
    return result  # 用户需要等待 30 秒
```

```python
# 使用 Celery 异步处理 - 用户体验好
@app.post("/generate-image")
def generate_image(prompt):
    # 立即返回任务 ID
    task = ai_generate_image.delay(prompt)  # 非阻塞，立即返回
    return {"task_id": task.id, "status": "PENDING"}  # 用户立即得到响应
```

### Celery 的核心优势

- ✅ **异步处理**: 不阻塞主线程
- ✅ **分布式**: 多个 Worker 并行处理
- ✅ **可靠性**: 任务失败自动重试
- ✅ **监控**: 完整的任务状态跟踪
- ✅ **扩展性**: 水平扩展 Worker 数量

---

## 2. 核心概念

### 2.1 基本组件

```
┌─────────────┐    消息    ┌─────────────┐    任务    ┌─────────────┐
│   Producer  │  ------>  │    Broker   │  ------>  │   Consumer  │
│  (生产者)    │           │  (消息队列)  │           │  (消费者)    │
│  FastAPI     │           │   Redis     │           │  Celery     │
└─────────────┘           └─────────────┘           └─────────────┘
       |                          |                           |
       |                          ↓                           ↓
       |                   ┌─────────────┐           ┌─────────────┐
       |                   │    Queue    │           │    Worker    │
       |                   │  (任务队列)  │           │  (工作进程)  │
       └───────────────────▶└─────────────┘◀──────────└─────────────┘
```

### 2.2 关键术语解释

| 术语 | 说明 | 示例 |
|------|------|------|
| **Task** | 要执行的工作单元 | `send_email_task.delay()` |
| **Worker** | 执行任务的进程 | `celery worker -A app` |
| **Broker** | 消息中间件，存储任务 | Redis、RabbitMQ |
| **Backend** | 存储任务结果的地方 | Redis、数据库 |
| **Queue** | 任务队列，按优先级分类 | `default`, `high_priority` |

### 2.3 我们项目中的组件

基于当前代码：

```python
# 生产者：FastAPI 应用
@router.post("/tasks")
async def create_task(task_in: TaskCreate):
    task = await task_crud.create_task(db=db, obj_in=task_in)

    # 触发异步任务
    run_ai_text_generation.delay(  # 🎯 这里是关键！
        task_id=str(task.id),
        prompt=task.prompt,
        model=task.model
    )
    return task

# 消息队列：Redis
celery_broker_url = "redis://localhost:6379/1"

# 消费者：Celery Worker
celery -A app.worker worker --loglevel=info

# 任务定义：AI 文本生成
@celery_app.task(bind=True, name="run_ai_text_generation")
def run_ai_text_generation(self, task_id: str, prompt: str, model: str):
    # 实际的 AI 处理逻辑
    pass
```

---

## 3. 环境搭建

### 3.1 安装依赖

在我们的项目中，依赖已经配置在 [`pyproject.toml`](pyproject.toml:19-21):

```toml
dependencies = [
    # ... 其他依赖
    "celery[redis]>=5.3.0",    # Celery 核心和 Redis 支持
    "redis>=5.0.0",            # Redis Python 客户端
    "flower>=2.0.0",           # Celery 监控工具
]
```

**安装命令**：
```bash
# 使用 uv（我们的项目推荐）
uv sync

# 或者使用 pip
pip install "celery[redis]>=5.3.0" "redis>=5.0.0" "flower>=2.0.0"
```

### 3.2 启动 Redis 服务

```bash
# 使用 Docker 启动 Redis（推荐）
docker run -d --name redis-ai-task -p 6379:6379 redis:7-alpine

# 验证 Redis 连接
docker exec redis-ai-task redis-cli ping
# 应该返回: PONG
```

### 3.3 项目结构

我们采用了清晰的模块化结构：

```
app/
├── worker/
│   ├── __init__.py          # 导出 celery_app
│   ├── app.py              # 🔑 Celery 应用配置
│   └── tasks/
│       ├── __init__.py
│       ├── ai_tasks.py     # AI 相关任务
│       └── demo_tasks.py   # 演示任务
├── api/v1/endpoints/
│   └── tasks.py            # 🎯 FastAPI 集成点
├── crud/
│   └── task.py             # 数据库操作
└── database.py             # 同步/异步数据库会话
```

---

## 4. 基础配置

### 4.1 Celery 应用配置

**文件位置**: [`app/worker/app.py`](app/worker/app.py)

```python
from celery import Celery
from app.core.config import settings

# 🔑 创建 Celery 应用实例
celery_app = Celery(
    "async_ai_task_runner",              # 应用名称
    broker=settings.celery_broker_url,  # 消息代理
    backend=settings.celery_result_backend,  # 结果存储
    include=[                           # 包含的任务模块
        "app.worker.tasks.ai_tasks",
        "app.worker.tasks.demo_tasks"
    ]
)

# ⚙️ 高级配置
celery_app.conf.update(
    # 序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # 任务路由配置
    task_routes={
        "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.worker.tasks.demo_tasks.*": {"queue": "demo_tasks"},
    },

    # 性能配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # 结果过期时间（24小时）
    result_expires=3600,

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)
```

### 4.2 配置文件说明

| 配置项 | 说明 | 我们的值 |
|--------|------|----------|
| `broker` | Redis 连接地址 | `redis://localhost:6379/1` |
| `backend` | 结果存储地址 | `redis://localhost:6379/2` |
| `task_serializer` | 任务序列化格式 | `json` |
| `timezone` | 时区设置 | `UTC` |
| `task_routes` | 任务路由规则 | 按 类型 分组 |

### 4.3 环境变量配置

**文件位置**: [`app/core/config.py`](app/core/config.py:13-16)

```python
class Settings(BaseSettings):
    # Redis & Celery 配置
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"      # 任务队列
    celery_result_backend: str = "redis://localhost:6379/2"  # 结果存储
```

---

## 5. 创建第一个任务

### 5.1 简单任务定义

**文件位置**: [`app/worker/tasks/demo_tasks.py`](app/worker/tasks/demo_tasks.py:11-25)

```python
from app.worker.app import celery_app
import time

@celery_app.task(name="simple_calculation")
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
    else:
        raise ValueError(f"不支持的操作: {operation}")

    print(f"✅ 计算结果: {result}")

    return {
        "operation": f"{a} {operation} {b}",
        "result": result,
        "timestamp": time.time()
    }
```

### 5.2 带进度的任务

**文件位置**: [`app/worker/tasks/ai_tasks.py`](app/worker/tasks/ai_tasks.py:12-55)

```python
from app.worker.app import celery_app
from app.models import TaskStatus
from app.crud.task import update_task_status, update_task_result
import time
import random

@celery_app.task(bind=True, name="run_ai_text_generation")
def run_ai_text_generation(self, task_id: str, prompt: str, model: str = "gpt-3.5-turbo"):
    """
    🤖 AI 文本生成任务
    支持进度跟踪和状态更新
    """
    try:
        print(f"🤖 开始处理AI文本生成任务: {task_id}")
        print(f"📝 Prompt: {prompt}")
        print(f"🧠 Model: {model}")

        # 1. 更新任务状态为处理中
        update_task_status(task_id, TaskStatus.PROCESSING)

        # 2. 模拟AI处理时间（5-15秒）
        processing_time = random.uniform(5, 15)
        print(f"⏳ 预计处理时间: {processing_time:.1f}秒")

        # 3. 🔑 进度跟踪（这是高级功能！）
        for i in range(int(processing_time)):
            time.sleep(1)
            progress = int((i + 1) / processing_time * 100)

            # 更新任务进度
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': int(processing_time),
                    'progress': progress,
                    'status': f'处理中... {progress}%'
                }
            )

        # 4. 生成AI结果
        if "天气" in prompt.lower():
            result = f"根据您的问题'{prompt}'，AI分析：今天天气晴朗，气温25°C。"
        elif "计算" in prompt.lower():
            result = f"AI数学助手：针对'{prompt}'的计算结果是42。"
        else:
            result = f"AI智能回复：关于'{prompt}'，这是我的深度分析..."

        # 5. 更新数据库中的任务结果
        update_task_result(task_id, TaskStatus.COMPLETED, result)

        print(f"✅ AI文本生成任务完成: {task_id}")

        # 6. 返回结果
        return {
            'task_id': task_id,
            'status': 'completed',
            'result': result,
            'processing_time': processing_time
        }

    except Exception as e:
        error_msg = f"AI文本生成失败: {str(e)}"
        print(f"❌ {error_msg}")

        # 更新任务状态为失败
        update_task_result(task_id, TaskStatus.FAILED, error_msg)

        # 任务失败，抛出异常让Celery重试机制生效
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

### 5.3 任务装饰器详解

```python
# 基础任务装饰器
@celery_app.task
def basic_task():
    pass

# 带名称的任务（推荐）
@celery_app.task(name="my_custom_task_name")
def named_task():
    pass

# 绑定任务实例（用于进度跟踪）
@celery_app.task(bind=True)
def bound_task(self):
    # self 包含任务信息
    print(f"Task ID: {self.request.id}")
    print(f"Retry count: {self.request.retries}")

    # 更新进度
    self.update_state(state='PROGRESS', meta={'progress': 50})

# 带重试的任务
@celery_app.task(bind=True, max_retries=3)
def retry_task(self):
    try:
        # 可能失败的操作
        risky_operation()
    except Exception as exc:
        # 重试，延迟60秒
        raise self.retry(exc=exc, countdown=60)

# 带优先级的任务
@celery_app.task(priority=5)
def priority_task():
    pass
```

---

## 6. 运行和监控

### 6.1 启动 Celery Worker

```bash
# 基础启动命令
celery -A app.worker worker --loglevel=info

# 指定并发数（推荐）
celery -A app.worker worker --loglevel=info --concurrency=4

# 启动多个Worker进程
celery -A app.worker worker --loglevel=info --concurrency=2 &
celery -A app.worker worker --loglevel=info --concurrency=2 &

# 启动特定队列的Worker
celery -A app.worker worker --loglevel=info --queues=ai_processing

# 后台运行（生产环境）
celery -A app.worker worker --loglevel=info --detach
```

### 6.2 监控工具：Flower

```bash
# 启动 Flower 监控面板
celery -A app.worker flower --port=5555

# 访问监控界面
# http://localhost:5555
```

**Flower 功能**：
- 📊 实时任务统计
- 👥 Worker 状态监控
- 📈 任务执行历史
- 🔧 任务管理（重试、撤销等）

### 6.3 命令行管理

```bash
# 查看活动任务
celery -A app.worker inspect active

# 查看注册的任务
celery -A app.worker inspect registered

# 查看Worker统计信息
celery -A app.worker inspect stats

# 查看队列长度
# 需要 redis-cli
docker exec redis-ai-task redis-cli llen celery
```

### 6.4 代码中的任务调用

```python
# 🎯 直接调用（推荐）
from app.worker.tasks.demo_tasks import simple_calculation

# 立即异步执行
result = simple_calculation.delay(10, 20, "add")
print(f"任务ID: {result.id}")

# 等待结果
if result.ready():
    print(f"结果: {result.get()}")

# 设置超时
try:
    result = result.get(timeout=10)
except Exception as e:
    print(f"任务超时或失败: {e}")

# 获取任务状态
print(f"状态: {result.status}")
print(f"结果: {result.result}")

# 取消任务
result.revoke(terminate=True)
```

---

## 7. 高级特性

### 7.1 任务路由

**配置**: [`app/worker/app.py`](app/worker/app.py:24-30)

```python
celery_app.conf.update(
    task_routes={
        "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.worker.tasks.demo_tasks.*": {"queue": "demo_tasks"},
        "app.worker.tasks.urgent.*": {"queue": "urgent"},
    }
)
```

**使用**：
```bash
# 启动专门处理AI任务的Worker
celery -A app.worker worker --queues=ai_processing --concurrency=2

# 启动专门处理紧急任务的Worker
celery -A app.worker worker --queues=urgent --concurrency=1
```

### 7.2 任务链 (Chain)

```python
from celery import chain

# 定义任务链
task_chain = chain(
    process_data.s(raw_data),
    analyze_results.s(),
    generate_report.s()
)

# 执行任务链
result = task_chain()
print(f"最终结果: {result.get()}")
```

### 7.3 任务组 (Group)

```python
from celery import group

# 并行执行多个任务
job = group([
    process_item.s(item) for item in items
])

# 执行任务组
result = job()
print(f"所有结果: {result.get()}")
```

### 7.4 定时任务 (Beat)

```python
from celery.schedules import crontab

# 配置定时任务
celery_app.conf.beat_schedule = {
    'daily-cleanup': {
        'task': 'cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
    'hourly-stats': {
        'task': 'generate_hourly_stats',
        'schedule': crontab(minute=0),  # 每小时
    },
}
```

**启动 Beat 调度器**：
```bash
celery -A app.worker beat --loglevel=info
```

### 7.5 任务优先级

```python
# 定义高优先级任务
@celery_app.task(priority=9)
def high_priority_task():
    pass

# 定义低优先级任务
@celery_app.task(priority=1)
def low_priority_task():
    pass

# Worker 配置支持优先级
celery -A app.worker worker --loglevel=info -Ofair
```

---

## 8. 错误处理

### 8.1 异常处理模式

**文件位置**: [`app/worker/tasks/ai_tasks.py`](app/worker/tasks/ai_tasks.py:52-65)

```python
@celery_app.task(bind=True, max_retries=3)
def robust_task(self, data):
    try:
        # 可能失败的操作
        result = process_data(data)
        return result
    except ConnectionError as exc:
        # 网络错误，重试
        raise self.retry(exc=exc, countdown=60)
    except ValueError as exc:
        # 数据错误，不重试，直接失败
        raise exc
    except Exception as exc:
        # 其他错误，重试
        raise self.retry(exc=exc, countdown=60)
```

### 8.2 重试策略

```python
# 指数退避重试
@celery_app.task(bind=True, max_retries=5)
def exponential_backoff_task(self):
    try:
        risky_operation()
    except Exception as exc:
        # 2^retry_count 延迟
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)

# 固定延迟重试
@celery_app.task(bind=True, max_retries=3)
def fixed_delay_task(self):
    try:
        risky_operation()
    except Exception as exc:
        # 固定延迟60秒
        raise self.retry(exc=exc, countdown=60)
```

### 8.3 任务超时

```python
# 任务级别超时
@celery_app.task(time_limit=300)  # 5分钟超时
def long_running_task():
    pass

# 应用级别超时配置
celery_app.conf.update(
    task_soft_time_limit=240,  # 软超时（4分钟）
    task_time_limit=300,       # 硬超时（5分钟）
)
```

### 8.4 结果后处理

```python
@celery_app.task(bind=True)
def task_with_callback(self, data):
    result = process_data(data)

    # 任务完成后执行回调
    if result:
        on_success.delay(result)
    else:
        on_failure.delay(data)

    return result

@celery_app.task
def on_success(result):
    print(f"任务成功: {result}")

@celery_app.task
def on_failure(data):
    print(f"任务失败，重新调度: {data}")
    retry_task.delay(data)
```

---

## 9. 最佳实践

### 9.1 任务设计原则

```python
# ✅ 好的任务设计
@celery_app.task(bind=True, max_retries=3)
def well_designed_task(self, data):
    """
    设计良好的任务
    """
    # 1. 参数验证
    if not data:
        raise ValueError("数据不能为空")

    # 2. 幂等性检查
    if already_processed(data['id']):
        return get_existing_result(data['id'])

    try:
        # 3. 原子性操作
        result = process_data(data)
        save_result(data['id'], result)
        return result
    except Exception as exc:
        # 4. 适当的错误处理
        logger.error(f"任务处理失败: {exc}")
        raise self.retry(exc=exc, countdown=60)

# ❌ 避免的任务设计
@celery_app.task
def bad_task():
    # 1. 全局状态依赖
    global some_global_var

    # 2. 长时间运行（无超时）
    while True:
        pass

    # 3. 没有错误处理
    risky_operation()

    # 4. 不幂等
    send_email()
```

### 9.2 性能优化

```python
# 1. 批量处理
@celery_app.task
def batch_process(items):
    """批量处理多个项目"""
    for item in items:
        process_item(item)
    return len(items)

# 2. 任务分片
def process_large_dataset(data):
    """将大任务分解为小任务"""
    chunk_size = 100
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

    # 并行处理所有块
    job = group(batch_process.s(chunk) for chunk in chunks)
    return job()

# 3. 预取优化
# Worker 启动参数
# celery -A app.worker worker --prefetch-multiplier=1

# 4. 连接池优化
celery_app.conf.update(
    broker_pool_limit=10,
    broker_connection_timeout=30,
)
```

### 9.3 监控和日志

```python
import logging
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery_app.task(bind=True)
def monitored_task(self, data):
    logger.info(f"开始处理任务 {self.request.id}")
    logger.info(f"数据大小: {len(data)}")

    try:
        result = process_data(data)
        logger.info(f"任务完成 {self.request.id}")
        return result
    except Exception as exc:
        logger.error(f"任务失败 {self.request.id}: {exc}")
        raise

# 配置日志
celery_app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)
```

### 9.4 生产环境配置

```python
# 生产环境配置
celery_app.conf.update(
    # 可靠性配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    # 性能配置
    worker_disable_rate_limits=False,
    task_compression='gzip',

    # 安全配置
    broker_transport_options={
        'visibility_timeout': 3600,  # 1小时
        'retry_policy': {
            'timeout': 5.0
        }
    }
)

# 启动命令（生产环境）
# celery -A app.worker worker --loglevel=info --concurrency=4 --max-tasks-per-child=1000
```

---

## 10. 常见问题

### 10.1 任务不执行

**问题**: 任务提交后没有执行

**排查步骤**:
```bash
# 1. 检查Worker状态
celery -A app.worker inspect active

# 2. 检查队列长度
docker exec redis-ai-task redis-cli llen celery

# 3. 检查Worker日志
# 查看Worker输出，看是否有错误

# 4. 检查任务注册
celery -A app.worker inspect registered
```

### 10.2 数据库连接问题

**问题**: Celery 任务中数据库连接失败

**解决方案**:
```python
# ✅ 使用同步数据库会话
from app.database import get_sync_db_session

@celery_app.task
def db_task():
    with get_sync_db_session() as db:
        # 同步数据库操作
        result = db.query(Task).first()
    return result
```

### 10.3 内存泄漏

**问题**: Worker 内存持续增长

**解决方案**:
```bash
# 限制每个Worker处理的任务数
celery -A app.worker worker --max-tasks-per-child=1000

# 定期重启Worker
# 使用supervisor等进程管理工具
```

### 10.4 任务重复执行

**问题**: 相同任务被执行多次

**解决方案**:
```python
# 确保任务幂等性
@celery_app.task
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

### 10.5 性能问题

**问题**: 任务执行太慢

**优化建议**:
```python
# 1. 分析任务瓶颈
@celery_app.task(bind=True)
def profile_task(self, data):
    import cProfile
    import io

    pr = cProfile.Profile()
    pr.enable()

    result = expensive_operation(data)

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()

    logger.info(f"性能分析:\n{s.getvalue()}")
    return result
```

---

## 🎯 总结

通过这个教程，您已经学会了：

1. ✅ **Celery 基础概念**: 理解了 Producer-Consumer 模式
2. ✅ **环境搭建**: 配置了 Redis 和 Celery 应用
3. ✅ **任务创建**: 编写了各种类型的任务
4. ✅ **运行监控**: 启动 Worker 和 Flower 监控
5. ✅ **高级特性**: 路由、重试、进度跟踪
6. ✅ **错误处理**: 异常捕获和重试机制
7. ✅ **最佳实践**: 性能优化和生产配置

### 下一步学习建议

1. **深入学习**: 阅读 [Celery 官方文档](https://docs.celeryproject.org/)
2. **实践项目**: 尝试实现邮件发送、图像处理等实际场景
3. **性能调优**: 根据实际负载调整配置参数
4. **监控集成**: 集成 Prometheus、Grafana 等监控工具

### 我们项目中的完整实现

当前项目包含了一个完整的 Celery 实现：

- 📁 **配置**: [`app/worker/app.py`](app/worker/app.py) - 完整的 Celery 配置
- 🔧 **任务**: [`app/worker/tasks/`](app/worker/tasks/) - AI 任务和演示任务
- 🌐 **集成**: [`app/api/v1/endpoints/tasks.py`](app/api/v1/endpoints/tasks.py) - FastAPI 集成
- 💾 **数据**: [`app/crud/task.py`](app/crud/task.py) - 数据库操作
- 🧪 **测试**: [`quick_test.py`](quick_test.py) - 功能验证

这已经是一个生产就绪的 Celery 实现，可以直接作为参考和学习材料！🚀