# 🌐 MCP Server Integration Tests
"""
Comprehensive MCP (Model Context Protocol) server tests for Async AI Task Runner.
Tests MCP protocol implementation, tool handling, resource management, and prompt processing.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
import asyncio
from datetime import datetime

# MCP imports
from mcp.types import (
    CallToolRequest, CallToolResult, TextContent,
    ListToolsRequest, ListToolsResult, Tool,
    ListResourcesRequest, ListResourcesResult, Resource,
    ListPromptsRequest, ListPromptsResult, Prompt
)
from mcp.server.models import InitializationOptions

# Application imports
from app.mcp.server import AsyncAITaskRunnerMCPServer, mcp_server
from app.database import AsyncSessionLocal
from app.models import Task
from app.schemas import TaskCreate, TaskStatus
from conftest import test_db_session, task_factory


class TestMCPServerInitialization:
    """Test MCP server initialization and configuration."""

    @pytest.mark.unit
    def test_mcp_server_initialization(self):
        """Test MCP server is properly initialized."""
        server = AsyncAITaskRunnerMCPServer()

        assert server.server is not None
        assert server.server.name == "async-ai-task-runner"
        assert hasattr(server, '_setup_handlers')

    @pytest.mark.unit
    def test_mcp_server_global_instance(self):
        """Test global MCP server instance."""
        assert mcp_server is not None
        assert isinstance(mcp_server, AsyncAITaskRunnerMCPServer)

    @pytest.mark.unit
    def test_mcp_handlers_setup(self):
        """Test that MCP protocol handlers are properly set up."""
        server = AsyncAITaskRunnerMCPServer()

        # Check that handlers are registered
        assert hasattr(server.server, 'list_tools')
        assert hasattr(server.server, 'call_tool')
        assert hasattr(server.server, 'list_resources')
        assert hasattr(server.server, 'list_prompts')


class TestMCPToolsListing:
    """Test MCP tools listing functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available MCP tools."""
        server = AsyncAITaskRunnerMCPServer()
        tools = await server.handle_list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 4  # create_task, get_task_status, list_tasks, get_task_result

        # Verify tool structure
        tool_names = [tool.name for tool in tools]
        expected_tools = ["create_task", "get_task_status", "list_tasks", "get_task_result"]
        assert all(name in tool_names for name in expected_tools)

        # Verify create_task tool
        create_task_tool = next(tool for tool in tools if tool.name == "create_task")
        assert create_task_tool.description is not None
        assert "properties" in create_task_tool.inputSchema
        assert "prompt" in create_task_tool.inputSchema["properties"]
        assert "prompt" in create_task_tool.inputSchema["required"]

        # Verify get_task_status tool
        get_status_tool = next(tool for tool in tools if tool.name == "get_task_status")
        assert get_status_tool.description is not None
        assert "task_id" in get_status_tool.inputSchema["properties"]
        assert "task_id" in get_status_tool.inputSchema["required"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tools_input_schema_validation(self):
        """Test that tool input schemas are valid JSON schemas."""
        server = AsyncAITaskRunnerMCPServer()
        tools = await server.handle_list_tools()

        for tool in tools:
            # Verify basic schema structure
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema
            assert "required" in tool.inputSchema

            # Verify required fields are defined in properties
            for required_field in tool.inputSchema["required"]:
                assert required_field in tool.inputSchema["properties"]

            # Verify property definitions
            for prop_name, prop_def in tool.inputSchema["properties"].items():
                assert "type" in prop_def
                assert "description" in prop_def

                # Check for enum values where applicable
                if "enum" in prop_def:
                    assert isinstance(prop_def["enum"], list)
                    assert len(prop_def["enum"]) > 0

                # Check for numeric constraints
                if prop_def["type"] in ["integer", "number"]:
                    if "minimum" in prop_def:
                        assert isinstance(prop_def["minimum"], (int, float))
                    if "maximum" in prop_def:
                        assert isinstance(prop_def["maximum"], (int, float))

                # Check for string constraints
                if prop_def["type"] == "string":
                    if "minLength" in prop_def:
                        assert isinstance(prop_def["minLength"], int)
                        assert prop_def["minLength"] >= 0
                    if "maxLength" in prop_def:
                        assert isinstance(prop_def["maxLength"], int)
                        assert prop_def["maxLength"] > prop_def.get("minLength", 0)


class TestMCPResourceListing:
    """Test MCP resources listing functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test listing available MCP resources."""
        server = AsyncAITaskRunnerMCPServer()
        resources = await server.handle_list_resources()

        assert isinstance(resources, list)
        assert len(resources) >= 3  # Should have at least 3 resources

        # Verify resource structure
        resource_uris = [resource.uri for resource in resources]
        expected_resources = [
            "data://tasks/schema",
            "data://tasks/statuses",
            "data://models/available"
        ]
        assert all(uri in resource_uris for uri in expected_resources)

        # Verify schema resource
        schema_resource = next(r for r in resources if r.uri == "data://tasks/schema")
        assert schema_resource.name == "任务对象Schema"
        assert "JSON Schema" in schema_resource.description
        assert schema_resource.mimeType == "application/json"

        # Verify statuses resource
        statuses_resource = next(r for r in resources if r.uri == "data://tasks/statuses")
        assert statuses_resource.name == "任务状态定义"
        assert "状态" in statuses_resource.description
        assert statuses_resource.mimeType == "application/json"

        # Verify models resource
        models_resource = next(r for r in resources if r.uri == "data://models/available")
        assert models_resource.name == "可用的AI模型"
        assert "模型" in models_resource.description
        assert models_resource.mimeType == "application/json"


class TestMCPPromptsListing:
    """Test MCP prompts listing functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_prompts(self):
        """Test listing available MCP prompts."""
        server = AsyncAITaskRunnerMCPServer()
        prompts = await server.handle_list_prompts()

        assert isinstance(prompts, list)
        assert len(prompts) >= 2  # Should have at least 2 prompts

        # Verify prompt structure
        prompt_names = [prompt.name for prompt in prompts]
        expected_prompts = ["task_summary", "system_health"]
        assert all(name in prompt_names for name in expected_prompts)

        # Verify task_summary prompt
        summary_prompt = next(p for p in prompts if p.name == "task_summary")
        assert summary_prompt.description is not None
        assert isinstance(summary_prompt.arguments, list)
        assert len(summary_prompt.arguments) >= 1

        # Check task_summary arguments
        task_ids_arg = next(arg for arg in summary_prompt.arguments if arg["name"] == "task_ids")
        assert task_ids_arg["description"] is not None
        assert not task_ids_arg.get("required", True)  # Should be optional

        # Verify system_health prompt
        health_prompt = next(p for p in prompts if p.name == "system_health")
        assert health_prompt.description is not None
        assert len(health_prompt.arguments) == 0  # No arguments required


class TestMCPToolExecution:
    """Test MCP tool execution functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_tool_success(self, test_db_session):
        """Test create_task tool execution with valid data."""
        server = AsyncAITaskRunnerMCPServer()

        arguments = {
            "prompt": "MCP test task creation",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "priority": 3
        }

        result = await server._handle_create_task(test_db_session, arguments)

        assert result.isError is False
        assert len(result.content) == 1
        assert result.content[0].type == "text"

        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True
        assert "task_id" in response_data
        assert response_data["status"] == "PENDING"
        assert response_data["message"] == "Task created successfully"

        # Verify task was actually created in database
        task_id = response_data["task_id"]
        db_task = await test_db_session.execute(
            select(Task).filter(Task.id == task_id)
        )
        created_task = db_task.scalar_one_or_none()
        assert created_task is not None
        assert created_task.prompt == arguments["prompt"]
        assert created_task.model == arguments["model"]
        assert created_task.provider == arguments["provider"]
        assert created_task.priority == arguments["priority"]
        assert created_task.status == TaskStatus.PENDING

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_tool_minimal_data(self, test_db_session):
        """Test create_task tool execution with minimal data."""
        server = AsyncAITaskRunnerMCPServer()

        arguments = {
            "prompt": "Minimal MCP task"
        }

        result = await server._handle_create_task(test_db_session, arguments)

        assert result.isError is False

        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True

        # Verify defaults were applied
        task_id = response_data["task_id"]
        db_task = await test_db_session.execute(
            select(Task).filter(Task.id == task_id)
        )
        created_task = db_task.scalar_one_or_none()
        assert created_task is not None
        assert created_task.prompt == arguments["prompt"]
        assert created_task.priority == 5  # Default priority
        assert created_task.model == "deepseek-chat"  # Default model
        assert created_task.provider == "deepseek"  # Default provider

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_task_tool_missing_prompt(self, test_db_session):
        """Test create_task tool execution without prompt."""
        server = AsyncAITaskRunnerMCPServer()

        arguments = {
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        result = await server._handle_create_task(test_db_session, arguments)

        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"

        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "message" in response_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_status_tool_success(self, test_db_session, task_factory):
        """Test get_task_status tool execution with existing task."""
        # Create a test task
        task = task_factory(
            prompt="MCP status test task",
            model="gpt-3.5-turbo",
            provider="openai",
            status=TaskStatus.PROCESSING
        )
        await test_db_session.commit()

        server = AsyncAITaskRunnerMCPServer()
        arguments = {"task_id": task.id}

        result = await server._handle_get_task_status(test_db_session, arguments)

        assert result.isError is False
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True

        task_info = response_data["task"]
        assert task_info["id"] == task.id
        assert task_info["prompt"] == task.prompt
        assert task_info["model"] == task.model
        assert task_info["provider"] == task.provider
        assert task_info["status"] == TaskStatus.PROCESSING.value
        assert task_info["priority"] == task.priority
        assert "created_at" in task_info

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_status_tool_not_found(self, test_db_session):
        """Test get_task_status tool execution with non-existent task."""
        server = AsyncAITaskRunnerMCPServer()
        arguments = {"task_id": 99999}

        result = await server._handle_get_task_status(test_db_session, arguments)

        assert result.isError is True
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is False
        assert "not found" in response_data["error"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_tasks_tool_success(self, test_db_session, task_factory):
        """Test list_tasks tool execution."""
        # Create test tasks with different statuses
        pending_task = task_factory(
            prompt="Pending MCP task",
            status=TaskStatus.PENDING,
            priority=2
        )
        completed_task = task_factory(
            prompt="Completed MCP task",
            status=TaskStatus.COMPLETED,
            priority=1
        )
        failed_task = task_factory(
            prompt="Failed MCP task",
            status=TaskStatus.FAILED,
            priority=3
        )
        await test_db_session.commit()

        server = AsyncAITaskRunnerMCPServer()

        # Test without filters
        arguments = {"limit": 10, "offset": 0}
        result = await server._handle_list_tasks(test_db_session, arguments)

        assert result.isError is False
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True

        tasks = response_data["tasks"]
        assert len(tasks) >= 3

        # Verify task structure
        for task in tasks:
            assert "id" in task
            assert "prompt" in task
            assert "status" in task
            assert "priority" in task
            assert "created_at" in task

        # Test with status filter
        arguments = {"status": "COMPLETED", "limit": 5, "offset": 0}
        result = await server._handle_list_tasks(test_db_session, arguments)

        assert result.isError is False
        response_data = json.loads(result.content[0].text)
        completed_tasks = [t for t in response_data["tasks"] if t["status"] == "COMPLETED"]
        assert len(completed_tasks) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_result_tool_success(self, test_db_session, task_factory):
        """Test get_task_result tool execution with completed task."""
        # Create a completed task
        task = task_factory(
            prompt="MCP result test task",
            model="gpt-3.5-turbo",
            provider="openai",
            status=TaskStatus.COMPLETED,
            result="This is the MCP test result content"
        )
        await test_db_session.commit()

        server = AsyncAITaskRunnerMCPServer()
        arguments = {"task_id": task.id}

        result = await server._handle_get_task_result(test_db_session, arguments)

        assert result.isError is False
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is True

        assert response_data["task_id"] == task.id
        assert response_data["prompt"] == task.prompt
        assert response_data["result"] == task.result
        assert response_data["model"] == task.model
        assert response_data["provider"] == task.provider
        assert "completed_at" in response_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_task_result_tool_not_completed(self, test_db_session, task_factory):
        """Test get_task_result tool with pending task."""
        # Create a pending task
        task = task_factory(
            prompt="Pending MCP result task",
            status=TaskStatus.PENDING
        )
        await test_db_session.commit()

        server = AsyncAITaskRunnerMCPServer()
        arguments = {"task_id": task.id}

        result = await server._handle_get_task_result(test_db_session, arguments)

        assert result.isError is True
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is False
        assert "not completed" in response_data["error"].lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unknown_tool_execution(self, test_db_session):
        """Test execution of unknown tool."""
        server = AsyncAITaskRunnerMCPServer()

        result = await server.handle_call_tool("unknown_tool", {"test": "data"})

        assert result.isError is True
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Unknown tool: unknown_tool" in result.content[0].text


class TestMCPErrorHandling:
    """Test MCP server error handling."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_with_database_error(self, test_db_session):
        """Test tool execution when database errors occur."""
        # Mock database error by closing session
        await test_db_session.close()

        server = AsyncAITaskRunnerMCPServer()
        arguments = {
            "prompt": "Database error test",
            "model": "gpt-3.5-turbo"
        }

        result = await server._handle_create_task(test_db_session, arguments)

        assert result.isError is True
        response_data = json.loads(result.content[0].text)
        assert response_data["success"] is False
        assert "error" in response_data
        assert "message" in response_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_with_invalid_arguments(self, test_db_session):
        """Test tool execution with invalid argument types."""
        server = AsyncAITaskRunnerMCPServer()

        # Test with non-integer task_id
        arguments = {"task_id": "invalid_id"}
        result = await server._handle_get_task_status(test_db_session, arguments)

        assert result.isError is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_with_missing_arguments(self, test_db_session):
        """Test tool execution with missing arguments."""
        server = AsyncAITaskRunnerMCPServer()

        # Test with no arguments for required tool
        arguments = {}
        result = await server._handle_get_task_status(test_db_session, arguments)

        assert result.isError is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_malformed_json_in_arguments(self):
        """Test handling of malformed JSON in tool arguments."""
        server = AsyncAITaskRunnerMCPServer()

        # This would normally be handled by MCP protocol layer
        # Test that our handlers can handle missing/None arguments
        with patch('app.database.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()

            result = await server.handle_call_tool("create_task", None)

            assert result.isError is True


class TestMCPProtocolCompliance:
    """Test MCP server protocol compliance."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_result_format(self):
        """Test that tool results follow MCP format."""
        server = AsyncAITaskRunnerMCPServer()

        # Mock database session
        with patch('app.database.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aexit__ = AsyncMock()

            # Test successful result
            result = await server._handle_create_task(
                mock_session.return_value.__aenter__.return_value,
                {"prompt": "Test format compliance"}
            )

            # Should be a CallToolResult
            assert hasattr(result, 'content')
            assert hasattr(result, 'isError')
            assert isinstance(result.content, list)

            # Content should be TextContent items
            if len(result.content) > 0:
                assert hasattr(result.content[0], 'type')
                assert hasattr(result.content[0], 'text')
                assert result.content[0].type == "text"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resource_metadata_compliance(self):
        """Test that resource metadata follows MCP format."""
        server = AsyncAITaskRunnerMCPServer()
        resources = await server.handle_list_resources()

        for resource in resources:
            # Should have required MCP resource fields
            assert hasattr(resource, 'uri')
            assert hasattr(resource, 'name')
            assert hasattr(resource, 'description')
            assert hasattr(resource, 'mimeType')

            # Fields should be strings
            assert isinstance(resource.uri, str)
            assert isinstance(resource.name, str)
            assert isinstance(resource.description, str)
            assert isinstance(resource.mimeType, str)

            # URI should be valid
            assert resource.uri.startswith("data://")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_prompt_metadata_compliance(self):
        """Test that prompt metadata follows MCP format."""
        server = AsyncAITaskRunnerMCPServer()
        prompts = await server.handle_list_prompts()

        for prompt in prompts:
            # Should have required MCP prompt fields
            assert hasattr(prompt, 'name')
            assert hasattr(prompt, 'description')
            assert hasattr(prompt, 'arguments')

            # Fields should have correct types
            assert isinstance(prompt.name, str)
            assert isinstance(prompt.description, str)
            assert isinstance(prompt.arguments, list)

            # Arguments should be properly structured
            for arg in prompt.arguments:
                assert isinstance(arg, dict)
                assert 'name' in arg
                assert 'description' in arg


class TestMCPConcurrencyAndPerformance:
    """Test MCP server concurrency and performance."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, test_db_session, task_factory):
        """Test concurrent tool execution."""
        server = AsyncAITaskRunnerMCPServer()

        # Create some initial tasks
        for _ in range(5):
            task_factory(prompt="Initial task")
        await test_db_session.commit()

        # Execute multiple tool calls concurrently
        tasks = [
            server._handle_list_tasks(test_db_session, {"limit": 5, "offset": 0})
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert result.isError is False

        # Each should return some tasks
        for result in results:
            response_data = json.loads(result.content[0].text)
            assert response_data["success"] is True
            assert "tasks" in response_data

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tool_execution_performance(self, test_db_session, performance_monitor):
        """Test tool execution performance."""
        server = AsyncAITaskRunnerMCPServer()

        # Test create_task performance
        with performance_monitor.measure("mcp_create_task"):
            result = await server._handle_create_task(
                test_db_session,
                {
                    "prompt": "MCP performance test",
                    "model": "gpt-3.5-turbo"
                }
            )

        assert result.isError is False

        # Test list_tasks performance
        with performance_monitor.measure("mcp_list_tasks"):
            result = await server._handle_list_tasks(
                test_db_session,
                {"limit": 10, "offset": 0}
            )

        assert result.isError is False

        measurements = performance_monitor.all_measurements()

        # Should complete quickly
        assert measurements.get("mcp_create_task", 0) < 1.0
        assert measurements.get("mcp_list_tasks", 0) < 0.5


class TestMCPServerLifecycle:
    """Test MCP server lifecycle and runtime behavior."""

    @pytest.mark.unit
    def test_server_run_method_exists(self):
        """Test that server has run method."""
        server = AsyncAITaskRunnerMCPServer()
        assert hasattr(server, 'run')
        assert callable(server.run)

    @pytest.mark.unit
    async def test_server_configuration(self):
        """Test server configuration parameters."""
        server = AsyncAITaskRunnerMCPServer()

        # Should be configurable for different hosts/ports
        with patch('mcp.server.stdio.stdio_server') as mock_stdio:
            mock_stdio.return_value = AsyncMock()

            # Should run without error
            await server.run(host="localhost", port=8001)

            # Should have been called with stdio transport
            mock_stdio.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_with_initialization_options(self):
        """Test server with proper MCP initialization options."""
        server = AsyncAITaskRunnerMCPServer()

        # Mock the stdio server to capture initialization
        with patch('mcp.server.stdio.stdio_server') as mock_stdio:
            async def mock_handle_client(stdin, stdout):
                # Mock server initialization
                await server.server.run(
                    stdin,
                    stdout,
                    InitializationOptions(
                        server_name="test-client",
                        server_version="1.0.0",
                        capabilities=server.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities=None,
                        ),
                    ),
                )

            mock_stdio.return_value = mock_handle_client
            await server.run()

            # Verify server was properly configured
            assert mock_stdio.called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])