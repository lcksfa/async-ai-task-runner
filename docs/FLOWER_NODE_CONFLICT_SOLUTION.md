# Flower 节点名称冲突解决方案

## 🎯 问题描述

启动 Flower 时出现警告：
```
DuplicateNodenameWarning: Received multiple replies from node name: celery@lizhaodeMacBook-Pro.local.
Please make sure you give each node a unique nodename using
the celery worker `-n` option.
```

## 🔍 问题原因

多个 Celery worker 进程使用相同的节点名称 `celery@hostname`，导致 Flower 无法区分不同的 worker 节点。

## ✅ 解决方案

### 1. 清理现有进程

```bash
# 停止所有 Celery 进程
pkill -f "celery.*worker"
pkill -f "celery.*flower"
```

### 2. 启动具有唯一名称的 Worker

```bash
# 方法一：使用 -n 参数指定唯一节点名称
celery -A app.worker worker --loglevel=info --concurrency=2 -n worker1@%h

# 方法二：启动多个专用 worker（按队列分离）
celery -A app.worker worker --queues=ai_processing -n ai-worker@%h
celery -A app.worker worker --queues=demo_tasks -n demo-worker@%h

# 参数说明：
# - worker1@%h: worker1 是自定义名称，%h 会自动替换为主机名
# - ai-worker@%h: 专门处理 AI 任务的 worker
# - demo-worker@%h: 专门处理演示任务的 worker
```

### 3. 启动 Flower（无警告）

```bash
# 现在启动 Flower 不会出现节点名称冲突警告
celery -A app.worker flower --port=5555
```

访问 http://localhost:5555 查看监控面板。

## 🎯 推荐的生产配置

### 单个 Worker（基础使用）
```bash
celery -A app.worker worker \
    --loglevel=info \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    -n main-worker@%h
```

### 多个 Worker（高并发）
```bash
# AI 任务专用 Worker
celery -A app.worker worker \
    --queues=ai_processing \
    --concurrency=2 \
    -n ai-worker@%h &

# 演示任务专用 Worker
celery -A app.worker worker \
    --queues=demo_tasks \
    --concurrency=1 \
    -n demo-worker@%h &

# 紧急任务专用 Worker
celery -A app.worker worker \
    --queues=urgent \
    --concurrency=1 \
    -n urgent-worker@%h &
```

## 📊 验证配置

### 1. 检查 Worker 状态
```bash
celery -A app.worker inspect active
```

### 2. 测试任务执行
```bash
python -c "
from app.worker.tasks.demo_tasks import simple_calculation
result = simple_calculation.delay(10, 20, 'add')
print(f'Task ID: {result.id}')
print(f'Result: {result.get(timeout=10)}')
"
```

### 3. 访问 Flower 监控面板
- **URL**: http://localhost:5555
- **功能**: 实时任务监控、Worker 状态、任务历史

## 🏆 最佳实践

1. **🔑 唯一命名**: 每个 worker 使用唯一的节点名称
2. **🎯 队列分离**: 不同类型任务使用专用 worker
3. **📊 监控集成**: 始终启用 Flower 进行监控
4. **⚡️ 性能调优**: 根据任务类型调整并发数

## 💡 高级技巧

### 自定义 Worker 命名规范
```bash
# 环境命名
-n prod-worker1@%h     # 生产环境
-n dev-worker1@%h      # 开发环境
-n test-worker1@%h     # 测试环境

# 功能命名
-n cpu-worker@%h       # CPU 密集型任务
-n io-worker@%h        # I/O 密集型任务
-n ai-worker@%h        # AI 处理任务
```

### 动态扩展 Worker
```bash
# 根据负载动态增加 worker
for i in {1..3}; do
    celery -A app.worker worker --concurrency=2 -n worker$i@%h &
done
```

这样配置后，Flower 将不再显示节点名称冲突警告，并且能够清楚地监控每个 worker 的状态和任务执行情况。