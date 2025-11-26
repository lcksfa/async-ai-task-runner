# Celery 快速参考手册

## 🚀 快速启动命令

```bash
# 1. 启动 Redis
docker run -d --name redis-ai-task -p 6379:6379 redis:7-alpine

# 2. 启动 Celery Worker
source .venv/bin/activate
celery -A app.worker worker --loglevel=info --concurrency=2

# 3. 启动 Flower 监控（可选）
celery -A app.worker flower --port=5555

# 4. 启动 FastAPI（另一个终端）
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 常用命令

### Worker 管理
```bash
# 查看活动任务
celery -A app.worker inspect active

# 查看注册的任务
celery -A app.worker inspect registered

# 查看Worker统计
celery -A app.worker inspect stats

# 重启Worker
celery -A app.worker control pool_restart
```

### 任务管理
```bash
# 撤销任务
celery -A app.worker control revoke <task_id> --terminate

# 清空队列
celery -A app.worker control purge

# 查看队列长度
docker exec redis-ai-task redis-cli llen celery
```

## 🧪 测试命令

```bash
# 运行快速测试
source .venv/bin/activate
python quick_test.py

# 测试特定任务
python -c "
from app.worker.tasks.demo_tasks import simple_calculation
result = simple_calculation.delay(10, 20, 'add')
print(f'任务ID: {result.id}')
print(f'结果: {result.get(timeout=10)}')
"
```

## 🔧 代码模板

### 1. 创建新任务

```python
# app/worker/tasks/your_tasks.py
from app.worker.app import celery_app

@celery_app.task(name="your_task_name")
def your_task(param1, param2):
    """任务描述"""
    try:
        # 任务逻辑
        result = do_something(param1, param2)
        return {"status": "success", "result": result}
    except Exception as e:
        # 错误处理
        raise

# 带重试的任务
@celery_app.task(bind=True, max_retries=3)
def retry_task(self, data):
    try:
        return process_data(data)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 2. 在FastAPI中调用任务

```python
# app/api/v1/endpoints/your_endpoint.py
from app.worker.tasks.your_tasks import your_task

@router.post("/process")
async def process_data(data: YourSchema):
    # 创建数据库记录
    db_record = await create_record(data)

    # 触发异步任务
    your_task.delay(
        record_id=str(db_record.id),
        data=data.dict()
    )

    return {"task_id": db_record.id, "status": "PENDING"}
```

### 3. 任务状态更新

```python
# app/crud/task.py 中的示例
def update_task_status(task_id, status):
    """更新任务状态"""
    from app.database import get_sync_db_session
    with get_sync_db_session() as db:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            db.commit()
            return True
    return False
```

## 📊 监控地址

- **Flower 监控**: http://localhost:5555
- **FastAPI 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## 🐛 常见问题解决

### 任务不执行
```bash
# 1. 检查Worker状态
celery -A app.worker inspect active

# 2. 检查任务注册
celery -A app.worker inspect registered | grep your_task_name

# 3. 查看Redis队列
docker exec redis-ai-task redis-cli llen celery
```

### 数据库连接问题
```python
# ✅ 正确的数据库使用方式
from app.database import get_sync_db_session

@celery_app.task
def db_task():
    with get_sync_db_session() as db:
        return db.query(Task).all()

# ❌ 错误的方式（不能在Celery中使用async）
@celery_app.task
async def bad_db_task():
    async with get_db() as db:
        return await db.query(Task).all()
```

### Worker 无响应
```bash
# 重启Worker
pkill -f "celery.*worker"
celery -A app.worker worker --loglevel=info --concurrency=2
```

## 🔧 配置参考

### app/core/config.py
```python
class Settings(BaseSettings):
    # Celery 配置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
```

### app/worker/app.py
```python
celery_app.conf.update(
    # 任务路由
    task_routes={
        "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.worker.tasks.urgent.*": {"queue": "urgent"},
    },

    # 性能配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # 重试配置
    task_soft_time_limit=300,
    task_time_limit=360,
)
```

## 📝 日志示例

### 成功的Worker启动
```
🚀 Celery应用已初始化
📡 Broker: redis://localhost:6379/1
💾 Backend: redis://localhost:6379/2

 -------------- celery@hostname v5.5.3
--- ***** -----
-- ******* ----
- ** ----------
- ** ----------
- ** ----------
-- ******* ----
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery
```

### 任务执行日志
```
[INFO] Task your_task[abc123] received
[INFO] Task your_task[abc123] succeeded in 2.5s: {'result': 'success'}
```

### 错误日志
```
[ERROR] Task your_task[def456] raised exception: ValueError('Invalid data')
[ERROR] Traceback (most recent call last):
  File "/app/worker/tasks/your_tasks.py", line 10, in your_task
    raise ValueError('Invalid data')
```

## 🎯 最佳实践检查清单

- [ ] 任务是幂等的（重复执行不会产生副作用）
- [ ] 有适当的错误处理和重试机制
- [ ] 使用同步数据库会话（不用async）
- [ ] 任务有明确的名称（@task(name="task_name")）
- [ ] 设置了合理的超时时间
- [ ] 日志记录充分
- [ ] 避免在任务中处理大量数据
- [ ] 使用任务路由进行负载均衡

## 📚 更多资源

- [Celery 官方文档](https://docs.celeryproject.org/)
- [Flower 监控文档](https://flower.readthedocs.io/)
- [Redis 文档](https://redis.io/documentation)
- [项目完整示例](./CELERY_BEGINNER_TUTORIAL.md)