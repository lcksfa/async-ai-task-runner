"""
Task Management Tools for MCP

Individual tool implementations for task management operations
exposed through Model Context Protocol.
"""

import json
import logging
from typing import Any, Dict, Optional, List
from mcp.types import TextContent

from app.database import get_db_session
from app.crud import task as task_crud
from app.schemas import TaskCreate
from app.mcp.config import validate_task_params, mcp_settings

logger = logging.getLogger(__name__)


class TaskToolsMixin:
    """Mixin class providing task management tools"""

    async def create_task_tool(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new AI processing task

        Args:
            arguments: Dictionary containing:
                - prompt (str, required): The AI prompt to process
                - model (str, optional): AI model to use
                - provider (str, optional): AI provider to use
                - priority (int, optional): Task priority from 1-10

        Returns:
            Dictionary with success status and task information
        """
        try:
            # Validate parameters
            is_valid, error_msg = validate_task_params(arguments)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": "VALIDATION_ERROR"
                }

            async with get_db_session() as db:
                # Create task object
                task_in = TaskCreate(
                    prompt=arguments["prompt"],
                    model=arguments.get("model", mcp_settings.default_model),
                    provider=arguments.get("provider", mcp_settings.default_provider),
                    priority=arguments.get("priority", mcp_settings.default_priority)
                )

                # Create task in database
                task = await task_crud.create_task(db=db, obj_in=task_in)

                logger.info(f"Created task {task.id} via MCP: {task.prompt[:50]}...")

                return {
                    "success": True,
                    "task_id": task.id,
                    "status": task.status,
                    "prompt": task.prompt,
                    "model": task.model,
                    "provider": task.provider,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "message": "Task created successfully"
                }

        except Exception as e:
            logger.error(f"Error creating task via MCP: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "CREATION_ERROR",
                "message": "Failed to create task"
            }

    async def get_task_status_tool(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get status and details of a specific task

        Args:
            arguments: Dictionary containing:
                - task_id (int, required): ID of task to retrieve

        Returns:
            Dictionary with success status and task details
        """
        try:
            if "task_id" not in arguments:
                return {
                    "success": False,
                    "error": "task_id is required",
                    "error_code": "MISSING_PARAMETER"
                }

            task_id = arguments["task_id"]
            if not isinstance(task_id, int) or task_id <= 0:
                return {
                    "success": False,
                    "error": "task_id must be a positive integer",
                    "error_code": "INVALID_PARAMETER"
                }

            async with get_db_session() as db:
                task = await task_crud.get_task(db=db, task_id=task_id)

                if not task:
                    return {
                        "success": False,
                        "error": f"Task with ID {task_id} not found",
                        "error_code": "TASK_NOT_FOUND"
                    }

                return {
                    "success": True,
                    "task": {
                        "id": task.id,
                        "prompt": task.prompt,
                        "status": task.status,
                        "model": task.model,
                        "provider": task.provider,
                        "priority": task.priority,
                        "result": task.result if task.status == "COMPLETED" else None,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None
                    }
                }

        except Exception as e:
            logger.error(f"Error getting task status via MCP: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "QUERY_ERROR",
                "message": "Failed to retrieve task status"
            }

    async def list_tasks_tool(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        List tasks with optional filtering and pagination

        Args:
            arguments: Dictionary containing optional parameters:
                - status (str, optional): Filter by task status
                - limit (int, optional): Maximum number of tasks to return
                - offset (int, optional): Number of tasks to skip

        Returns:
            Dictionary with success status and task list
        """
        try:
            # Extract and validate parameters
            limit = min(
                arguments.get("limit", mcp_settings.default_task_limit),
                mcp_settings.max_tasks_per_request
            )
            offset = max(arguments.get("offset", 0), 0)
            status = arguments.get("status")

            if status and status not in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]:
                return {
                    "success": False,
                    "error": f"Invalid status '{status}'. Valid statuses: PENDING, PROCESSING, COMPLETED, FAILED",
                    "error_code": "INVALID_PARAMETER"
                }

            async with get_db_session() as db:
                tasks = await task_crud.get_tasks(
                    db=db,
                    skip=offset,
                    limit=limit,
                    status=status
                )

                return {
                    "success": True,
                    "tasks": [
                        {
                            "id": task.id,
                            "prompt": (
                                task.prompt[:100] + "..."
                                if len(task.prompt) > 100
                                else task.prompt
                            ),
                            "status": task.status,
                            "model": task.model,
                            "provider": task.provider,
                            "priority": task.priority,
                            "created_at": task.created_at.isoformat() if task.created_at else None,
                            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                            "has_result": bool(task.result) if task.status == "COMPLETED" else False
                        }
                        for task in tasks
                    ],
                    "count": len(tasks),
                    "limit": limit,
                    "offset": offset,
                    "status_filter": status
                }

        except Exception as e:
            logger.error(f"Error listing tasks via MCP: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "QUERY_ERROR",
                "message": "Failed to retrieve tasks"
            }

    async def get_task_result_tool(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get result of a completed task

        Args:
            arguments: Dictionary containing:
                - task_id (int, required): ID of completed task

        Returns:
            Dictionary with success status and task result
        """
        try:
            if "task_id" not in arguments:
                return {
                    "success": False,
                    "error": "task_id is required",
                    "error_code": "MISSING_PARAMETER"
                }

            task_id = arguments["task_id"]
            if not isinstance(task_id, int) or task_id <= 0:
                return {
                    "success": False,
                    "error": "task_id must be a positive integer",
                    "error_code": "INVALID_PARAMETER"
                }

            async with get_db_session() as db:
                task = await task_crud.get_task(db=db, task_id=task_id)

                if not task:
                    return {
                        "success": False,
                        "error": f"Task with ID {task_id} not found",
                        "error_code": "TASK_NOT_FOUND"
                    }

                if task.status != "COMPLETED":
                    return {
                        "success": False,
                        "error": f"Task {task_id} is not completed (current status: {task.status})",
                        "error_code": "TASK_NOT_COMPLETED"
                    }

                return {
                    "success": True,
                    "task_id": task.id,
                    "prompt": task.prompt,
                    "result": task.result,
                    "model": task.model,
                    "provider": task.provider,
                    "priority": task.priority,
                    "completed_at": task.updated_at.isoformat() if task.updated_at else None
                }

        except Exception as e:
            logger.error(f"Error getting task result via MCP: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "QUERY_ERROR",
                "message": "Failed to retrieve task result"
            }


# Tool instance
task_tools = TaskToolsMixin()

# Export tool functions for direct access
async def create_task_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create task tool function"""
    return await task_tools.create_task_tool(arguments)


async def get_task_status_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get task status tool function"""
    return await task_tools.get_task_status_tool(arguments)


async def list_tasks_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List tasks tool function"""
    return await task_tools.list_tasks_tool(arguments)


async def get_task_result_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get task result tool function"""
    return await task_tools.get_task_result_tool(arguments)


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Get schemas for all task tools"""
    return [
        {
            "name": "create_task",
            "description": "Create a new AI processing task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": f"The AI prompt to process (1-{mcp_settings.max_task_prompt_length} characters)"
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use",
                        "enum": mcp_settings.allowed_models,
                        "default": mcp_settings.default_model
                    },
                    "provider": {
                        "type": "string",
                        "description": "AI provider to use",
                        "enum": mcp_settings.allowed_providers,
                        "default": mcp_settings.default_provider
                    },
                    "priority": {
                        "type": "integer",
                        "description": f"Task priority from 1-{mcp_settings.max_priority}",
                        "minimum": 1,
                        "maximum": mcp_settings.max_priority,
                        "default": mcp_settings.default_priority
                    }
                },
                "required": ["prompt"]
            }
        },
        {
            "name": "get_task_status",
            "description": "Get status and details of a specific task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of task to retrieve",
                        "minimum": 1
                    }
                },
                "required": ["task_id"]
            }
        },
        {
            "name": "list_tasks",
            "description": "List tasks with optional filtering and pagination",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by task status",
                        "enum": ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": f"Maximum number of tasks to return (1-{mcp_settings.max_tasks_per_request})",
                        "minimum": 1,
                        "maximum": mcp_settings.max_tasks_per_request,
                        "default": mcp_settings.default_task_limit
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of tasks to skip",
                        "minimum": 0,
                        "default": 0
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_task_result",
            "description": "Get result of a completed task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of completed task",
                        "minimum": 1
                    }
                },
                "required": ["task_id"]
            }
        }
    ]