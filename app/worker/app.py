"""
Celery应用配置
负责创建和配置Celery实例，作为异步任务处理的中央调度器
"""
from celery import Celery
from app.core.config import settings

# 创建Celery实例
celery_app = Celery(
    "async_ai_task_runner",

    # 消息代理配置（Redis）
    broker=settings.celery_broker_url,

    # 结果存储配置（Redis）
    backend=settings.celery_result_backend,

    # 包含任务定义的模块
    include=[
        "app.worker.tasks.ai_tasks",
        "app.worker.tasks.demo_tasks"
    ]
)

# Celery配置选项
celery_app.conf.update(
    # 任务序列化格式
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

    # 任务优先级
    task_inherit_parent_priority=True,
    task_default_priority=5,
    worker_prefetch_multiplier=1,

    # 结果过期时间（24小时）
    result_expires=3600,

    # 任务重试配置
    task_acks_late=True,
    worker_disable_rate_limits=False,

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)

print(f"🚀 Celery应用已初始化")
print(f"📡 Broker: {settings.celery_broker_url}")
print(f"💾 Backend: {settings.celery_result_backend}")