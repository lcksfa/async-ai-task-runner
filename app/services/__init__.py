"""
服务层模块
提供业务逻辑服务，包括AI服务、通知服务等
"""

from .ai_service import ai_service, AIService, AIProvider

__all__ = [
    "ai_service",
    "AIService",
    "AIProvider"
]