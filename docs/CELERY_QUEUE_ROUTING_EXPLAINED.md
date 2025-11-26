# Celery 任务队列路由详解

## 🎯 队列路由配置

```python
# app/worker/app.py
task_routes={
    "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
    "app.worker.tasks.demo_tasks.*": {"queue": "demo_tasks"},
}
```

## 🔄 实际运行分析

从刚才的测试可以看出两个队列的并行处理：

```
12:00:07,889 INFO Task run_ai_text_generation[AI任务ID] received
12:00:07,891 INFO Task simple_calculation[演示任务ID] received
```

**两个任务几乎同时被接收，但是由不同的 Worker 进程并行处理！**

## 📊 两个队列的详细对比

| 特性 | ai_processing 队列 | demo_tasks 队列 |
|------|-------------------|----------------|
| **任务类型** | `run_ai_text_generation` 等 | `simple_calculation` 等 |
| **处理时间** | 5-15秒 (10.6秒实测) | 1-3秒 (1.86秒实测) |
| **资源消耗** | 高 (CPU/内存密集) | 低 (轻量计算) |
| **并发度** | 可配置低并发 | 可配置高并发 |
| **Worker分配** | ForkPoolWorker-2 | ForkPoolWorker-1 |
| **数据库操作** | 频繁状态更新 | 简单或无DB操作 |
| **错误处理** | 需要重试机制 | 简单失败处理 |

## 🚀 队列路由的优势

### 1. **负载分离**
```python
# AI 任务不会阻塞简单任务
# 从日志看到：AI任务(10.6秒) 与 计算任务(1.86秒) 同时进行
```

### 2. **专用Worker配置**
```bash
# 可以启动不同配置的Worker
celery -A app.worker worker --queues=ai_processing --concurrency=1  # AI专用，低并发
celery -A app.worker worker --queues=demo_tasks --concurrency=4     # 演示专用，高并发
```

### 3. **故障隔离**
- AI任务失败不影响演示任务
- 可以独立重启不同队列的Worker
- 不同队列可以使用不同的资源限制

### 4. **监控精细化**
```python
# 在Flower中可以看到：
# - ai_processing 队列的任务处理统计
# - demo_tasks 队列的任务处理统计
```

## 🔧 生产环境推荐配置

### 高并发场景
```python
# 添加更多队列路由
task_routes={
    "app.worker.tasks.ai_tasks.*": {"queue": "ai_processing"},
    "app.worker.tasks.demo_tasks.*": {"queue": "demo_tasks"},
    "app.worker.tasks.urgent.*": {"queue": "urgent"},      # 紧急任务
    "app.worker.tasks.reports.*": {"queue": "reports"},    # 报表生成
    "app.worker.tasks.emails.*": {"queue": "notifications"}, # 邮件通知
}
```

### Worker启动策略
```bash
# 紧急任务 - 高优先级，专用Worker
celery -A app.worker worker --queues=urgent -n urgent-worker@%h --concurrency=1 &

# AI任务 - CPU密集，限制并发
celery -A app.worker worker --queues=ai_processing -n ai-worker@%h --concurrency=2 &

# 演示任务 - 轻量，高并发
celery -A app.worker worker --queues=demo_tasks -n demo-worker@%h --concurrency=4 &

# 通用任务 - 处理其他所有队列
celery -A app.worker worker --queues=celery,reports,notifications -n general-worker@%h --concurrency=3 &
```

## 📈 性能监控

### 查看队列状态
```bash
# 检查各个队列的长度
docker exec redis-ai-task redis-cli llen ai_processing
docker exec redis-ai-task redis-cli llen demo_tasks

# 查看Worker处理的队列
celery -A app.worker inspect active_queues
```

### Flower监控面板
- **URL**: http://localhost:5555
- **功能**:
  - 各队列任务数量统计
  - Worker处理速度对比
  - 任务失败率分析
  - 实时任务执行情况

## 🎯 实际应用场景

### 队分离的价值
1. **用户体验**: 简单任务(如用户验证)快速响应
2. **资源优化**: AI任务不阻塞轻量级操作
3. **扩展性**: 可以根据队列负载动态调整Worker数量
4. **维护性**: 不同类型任务可以独立升级和维护

### 业务示例
```python
# 用户注册时的任务分发
@router.post("/register")
async def register_user(user_data):
    # 立即创建用户记录
    user = create_user(user_data)

    # 异步处理不同任务
    send_welcome_email.delay(user.email)           # demo_tasks 队列 (快速)
    generate_user_profile.delay(user.id)           # ai_processing 队列 (慢)
    update_user_statistics.delay(user.id)          # demo_tasks 队列 (快速)

    return {"user_id": user.id, "status": "registered"}
```

## 🔍 总结

队列路由是 Celery 的核心优化特性，它让不同类型的任务能够：

- **并行处理**: AI任务和简单任务同时进行
- **资源优化**: 根据任务特点配置不同Worker
- **故障隔离**: 一个队列的问题不影响其他队列
- **精细监控**: 分别统计和分析各队列性能

这种设计在处理混合类型任务时特别有效，确保了系统的高并发性和稳定性！