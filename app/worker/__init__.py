# Celery Worker模块
# 包含Celery应用实例和所有异步任务定义

from .app import celery_app

__all__ = ["celery_app"]