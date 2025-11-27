"""
MCP Resources Implementation

Resources exposed through Model Context Protocol for external AI systems
to access structured data and schemas from Async AI Task Runner.
"""

from .task_resources import (
    task_schema_resource,
    task_statuses_resource,
    available_models_resource,
    system_stats_resource
)

__all__ = [
    "task_schema_resource",
    "task_statuses_resource",
    "available_models_resource",
    "system_stats_resource"
]