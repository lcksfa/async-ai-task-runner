"""
MCP (Model Context Protocol) Server Configuration

This module provides the main MCP server implementation for the Async AI Task Runner.
It exposes task management capabilities through the Model Context Protocol.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    Resource,
    TextContent,
    Tool,
)

from app.database import get_db_session
from app.crud import task as task_crud
from app.schemas import TaskCreate, TaskResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncAITaskRunnerMCPServer:
    """MCP Server for Async AI Task Runner"""

    def __init__(self):
        self.server = Server("async-ai-task-runner")
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="create_task",
                    description="Create a new AI processing task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The AI prompt to process",
                                "minLength": 1,
                                "maxLength": 1000
                            },
                            "model": {
                                "type": "string",
                                "description": "AI model to use (default: deepseek-chat)",
                                "default": "deepseek-chat",
                                "enum": ["deepseek-chat", "gpt-3.5-turbo", "gpt-4"]
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Task priority from 1-10",
                                "minimum": 1,
                                "maximum": 10,
                                "default": 5
                            },
                            "provider": {
                                "type": "string",
                                "description": "AI provider to use",
                                "default": "deepseek",
                                "enum": ["deepseek", "openai", "anthropic"]
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="get_task_status",
                    description="Get status and details of a specific task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "integer",
                                "description": "ID of the task to retrieve"
                            }
                        },
                        "required": ["task_id"]
                    }
                ),
                Tool(
                    name="list_tasks",
                    description="List tasks with optional filtering and pagination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Filter by task status",
                                "enum": ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of tasks to return",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10
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
                ),
                Tool(
                    name="get_task_result",
                    description="Get the result of a completed task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "integer",
                                "description": "ID of the completed task"
                            }
                        },
                        "required": ["task_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> CallToolResult:
            """Handle tool calls"""
            try:
                async with get_db_session() as db:
                    if name == "create_task":
                        return await self._handle_create_task(db, arguments or {})
                    elif name == "get_task_status":
                        return await self._handle_get_task_status(db, arguments or {})
                    elif name == "list_tasks":
                        return await self._handle_list_tasks(db, arguments or {})
                    elif name == "get_task_result":
                        return await self._handle_get_task_result(db, arguments or {})
                    else:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Unknown tool: {name}"
                                )
                            ],
                            isError=True
                        )
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error executing tool {name}: {str(e)}"
                        )
                    ],
                    isError=True
                )

        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="data://tasks/schema",
                    name="Task Schema",
                    description="JSON schema for task objects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="data://tasks/statuses",
                    name="Task Statuses",
                    description="Available task statuses and their meanings",
                    mimeType="application/json"
                ),
                Resource(
                    uri="data://models/available",
                    name="Available AI Models",
                    description="List of supported AI models and providers",
                    mimeType="application/json"
                )
            ]

        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="task_summary",
                    description="Generate a summary of task execution",
                    arguments=[
                        {
                            "name": "task_ids",
                            "description": "Comma-separated list of task IDs to summarize",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="system_health",
                    description="Generate a system health report",
                    arguments=[]
                )
            ]

    async def _handle_create_task(
        self, db, arguments: Dict[str, Any]
    ) -> CallToolResult:
        """Handle create task tool call"""
        try:
            task_in = TaskCreate(
                prompt=arguments["prompt"],
                model=arguments.get("model", "deepseek-chat"),
                priority=arguments.get("priority", 5),
                provider=arguments.get("provider", "deepseek")
            )

            task = await task_crud.create_task(db=db, obj_in=task_in)

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "task_id": task.id,
                            "status": task.status,
                            "message": "Task created successfully"
                        }, indent=2)
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e),
                            "message": "Failed to create task"
                        }, indent=2)
                    )
                ],
                isError=True
            )

    async def _handle_get_task_status(
        self, db, arguments: Dict[str, Any]
    ) -> CallToolResult:
        """Handle get task status tool call"""
        try:
            task_id = arguments["task_id"]
            task = await task_crud.get_task(db=db, task_id=task_id)

            if not task:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "success": False,
                                "error": f"Task with ID {task_id} not found"
                            }, indent=2)
                        )
                    ],
                    isError=True
                )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "task": {
                                "id": task.id,
                                "prompt": task.prompt,
                                "status": task.status,
                                "model": task.model,
                                "provider": task.provider,
                                "priority": task.priority,
                                "created_at": task.created_at.isoformat() if task.created_at else None,
                                "updated_at": task.updated_at.isoformat() if task.updated_at else None
                            }
                        }, indent=2)
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, indent=2)
                    )
                ],
                isError=True
            )

    async def _handle_list_tasks(
        self, db, arguments: Dict[str, Any]
    ) -> CallToolResult:
        """Handle list tasks tool call"""
        try:
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)
            status = arguments.get("status")

            tasks = await task_crud.get_tasks(
                db=db,
                skip=offset,
                limit=limit,
                status=status
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "tasks": [
                                {
                                    "id": task.id,
                                    "prompt": task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt,
                                    "status": task.status,
                                    "model": task.model,
                                    "provider": task.provider,
                                    "priority": task.priority,
                                    "created_at": task.created_at.isoformat() if task.created_at else None
                                } for task in tasks
                            ],
                            "count": len(tasks),
                            "limit": limit,
                            "offset": offset
                        }, indent=2)
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, indent=2)
                    )
                ],
                isError=True
            )

    async def _handle_get_task_result(
        self, db, arguments: Dict[str, Any]
    ) -> CallToolResult:
        """Handle get task result tool call"""
        try:
            task_id = arguments["task_id"]
            task = await task_crud.get_task(db=db, task_id=task_id)

            if not task:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "success": False,
                                "error": f"Task with ID {task_id} not found"
                            }, indent=2)
                        )
                    ],
                    isError=True
                )

            if task.status != "COMPLETED":
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "success": False,
                                "error": f"Task {task_id} is not completed (status: {task.status})"
                            }, indent=2)
                        )
                    ],
                    isError=True
                )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "task_id": task.id,
                            "prompt": task.prompt,
                            "result": task.result,
                            "model": task.model,
                            "provider": task.provider,
                            "completed_at": task.updated_at.isoformat() if task.updated_at else None
                        }, indent=2)
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": str(e)
                        }, indent=2)
                    )
                ],
                isError=True
            )

    async def run(self, host: str = "localhost", port: int = 8001):
        """Run the MCP server"""
        logger.info(f"Starting MCP server on {host}:{port}")

        # Run with stdio transport for Claude Desktop integration
        import sys
        from mcp.server.stdio import stdio_server

        async def handle_client(stdin, stdout):
            await self.server.run(
                stdin,
                stdout,
                InitializationOptions(
                    server_name="async-ai-task-runner",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

        await stdio_server(handle_client)


# Global server instance
mcp_server = AsyncAITaskRunnerMCPServer()

async def main():
    """Main entry point for MCP server"""
    await mcp_server.run()

if __name__ == "__main__":
    asyncio.run(main())