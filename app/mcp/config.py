"""
MCP Server Configuration

Configuration settings for Model Context Protocol server integration
with Async AI Task Runner.
"""

from typing import Dict, Any, Optional, List
from pydantic import Field


class MCPServerSettings:
    """MCP Server Configuration (simplified)"""

    # Server settings
    server_name: str = "async-ai-task-runner"
    server_version: str = "1.0.0"
    server_description: str = "异步AI任务运行器 - MCP服务器，用于AI任务管理"

    # Connection settings
    host: str = "localhost"
    port: int = 8001
    transport: str = "stdio"

    # Task management settings
    default_model: str = "deepseek-chat"
    default_provider: str = "deepseek"
    max_task_prompt_length: int = 1000
    max_priority: int = 10
    default_priority: int = 5

    # Resource limits
    max_tasks_per_request: int = 100
    default_task_limit: int = 10

    # Security settings
    allowed_models: List[str] = ["deepseek-chat", "gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
    allowed_providers: List[str] = ["deepseek", "openai", "anthropic"]

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Feature flags
    enable_task_creation: bool = True
    enable_task_status_queries: bool = True
    enable_task_listing: bool = True
    enable_task_result_access: bool = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class MCPResourceDefinitions:
    """MCP Resource definitions for the task runner"""

    TASK_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "description": "Unique task identifier"},
            "prompt": {
                "type": "string",
                "description": "AI prompt to process",
                "minLength": 1,
                "maxLength": 1000
            },
            "model": {
                "type": "string",
                "description": "AI model to use",
                "enum": ["deepseek-chat", "gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
            },
            "provider": {
                "type": "string",
                "description": "AI provider to use",
                "enum": ["deepseek", "openai", "anthropic"]
            },
            "status": {
                "type": "string",
                "description": "Current task status",
                "enum": ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
            },
            "priority": {
                "type": "integer",
                "description": "Task priority (1-10, higher is more urgent)",
                "minimum": 1,
                "maximum": 10
            },
            "result": {"type": "string", "description": "AI generated result (when completed)"},
            "created_at": {"type": "string", "format": "date-time", "description": "Task creation time"},
            "updated_at": {"type": "string", "format": "date-time", "description": "Last update time"}
        },
        "required": ["id", "prompt", "model", "provider", "status", "priority", "created_at", "updated_at"]
    }

    TASK_STATUSES = {
        "PENDING": {
            "description": "Task created, waiting to be processed",
            "color": "#FFA500",  # Orange
            "user_visible": True
        },
        "PROCESSING": {
            "description": "Task is currently being processed by AI",
            "color": "#007BFF",  # Blue
            "user_visible": True
        },
        "COMPLETED": {
            "description": "Task completed successfully with AI result",
            "color": "#28A745",  # Green
            "user_visible": True
        },
        "FAILED": {
            "description": "Task processing failed with error",
            "color": "#DC3545",  # Red
            "user_visible": True
        }
    }

    AVAILABLE_MODELS = {
        "deepseek": {
            "name": "deepseek-chat",
            "description": "DeepSeek AI chat model",
            "provider": "deepseek",
            "cost_per_token": 0.000001,
            "context_window": 32768,
            "recommended_for": ["general_qa", "coding", "analysis"]
        },
        "openai": {
            "name": "gpt-3.5-turbo",
            "description": "OpenAI GPT-3.5 Turbo model",
            "provider": "openai",
            "cost_per_token": 0.000002,
            "context_window": 16384,
            "recommended_for": ["general_qa", "creative_writing"]
        },
        "openai_gpt4": {
            "name": "gpt-4",
            "description": "OpenAI GPT-4 model",
            "provider": "openai",
            "cost_per_token": 0.00003,
            "context_window": 32768,
            "recommended_for": ["complex_analysis", "coding", "research"]
        }
    }


# Global settings instance
mcp_settings = MCPServerSettings()


def get_mcp_config() -> Dict[str, Any]:
    """Get complete MCP configuration as dictionary"""
    return {
        "server": {
            "name": mcp_settings.server_name,
            "version": mcp_settings.server_version,
            "description": mcp_settings.server_description
        },
        "connection": {
            "host": mcp_settings.host,
            "port": mcp_settings.port,
            "transport": mcp_settings.transport
        },
        "task_management": {
            "default_model": mcp_settings.default_model,
            "default_provider": mcp_settings.default_provider,
            "max_prompt_length": mcp_settings.max_task_prompt_length,
            "max_priority": mcp_settings.max_priority,
            "default_priority": mcp_settings.default_priority
        },
        "limits": {
            "max_tasks_per_request": mcp_settings.max_tasks_per_request,
            "default_task_limit": mcp_settings.default_task_limit
        },
        "security": {
            "allowed_models": mcp_settings.allowed_models,
            "allowed_providers": mcp_settings.allowed_providers
        },
        "features": {
            "enable_task_creation": mcp_settings.enable_task_creation,
            "enable_task_status_queries": mcp_settings.enable_task_status_queries,
            "enable_task_listing": mcp_settings.enable_task_listing,
            "enable_task_result_access": mcp_settings.enable_task_result_access
        }
    }


def validate_task_params(params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate task creation parameters"""
    if "prompt" not in params:
        return False, "Prompt is required"

    prompt = params["prompt"]
    if not isinstance(prompt, str) or len(prompt.strip()) == 0:
        return False, "Prompt must be a non-empty string"

    if len(prompt) > mcp_settings.max_task_prompt_length:
        return False, f"Prompt too long (max {mcp_settings.max_task_prompt_length} characters)"

    if "model" in params:
        model = params["model"]
        if model not in mcp_settings.allowed_models:
            return False, f"Model '{model}' not allowed. Allowed: {mcp_settings.allowed_models}"

    if "provider" in params:
        provider = params["provider"]
        if provider not in mcp_settings.allowed_providers:
            return False, f"Provider '{provider}' not allowed. Allowed: {mcp_settings.allowed_providers}"

    if "priority" in params:
        priority = params["priority"]
        if not isinstance(priority, int) or priority < 1 or priority > mcp_settings.max_priority:
            return False, f"Priority must be between 1 and {mcp_settings.max_priority}"

    return True, None