"""
Task Resources for MCP

Resource handlers for providing structured data about tasks,
schemas, and system information through Model Context Protocol.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from app.database import get_db_session
from app.crud import task as task_crud
from app.mcp.config import MCPResourceDefinitions, mcp_settings

logger = logging.getLogger(__name__)


class TaskResourcesMixin:
    """Mixin class providing task-related resources"""

    async def task_schema_resource(self) -> str:
        """
        Provide JSON schema for task objects

        Returns:
            JSON string containing task schema
        """
        try:
            schema = MCPResourceDefinitions.TASK_SCHEMA.copy()

            # Add usage examples
            schema["examples"] = [
                {
                    "id": 1,
                    "prompt": "Explain quantum computing in simple terms",
                    "model": "deepseek-chat",
                    "provider": "deepseek",
                    "status": "COMPLETED",
                    "priority": 5,
                    "result": "Quantum computing is a revolutionary approach...",
                    "created_at": "2025-11-27T03:00:00Z",
                    "updated_at": "2025-11-27T03:02:00Z"
                },
                {
                    "id": 2,
                    "prompt": "Write a Python function to calculate factorial",
                    "model": "gpt-4",
                    "provider": "openai",
                    "status": "PROCESSING",
                    "priority": 8,
                    "created_at": "2025-11-27T03:05:00Z",
                    "updated_at": "2025-11-27T03:05:00Z"
                }
            ]

            # Add validation rules
            schema["validation_rules"] = {
                "prompt": {
                    "required": True,
                    "min_length": 1,
                    "max_length": mcp_settings.max_task_prompt_length,
                    "pattern": ".*\\S+.*"  # At least one non-whitespace character
                },
                "status": {
                    "required": True,
                    "enum": list(MCPResourceDefinitions.TASK_STATUSES.keys())
                },
                "priority": {
                    "required": True,
                    "minimum": 1,
                    "maximum": mcp_settings.max_priority
                }
            }

            return json.dumps(schema, indent=2)

        except Exception as e:
            logger.error(f"Error generating task schema resource: {e}")
            return json.dumps({
                "error": str(e),
                "message": "Failed to generate task schema"
            }, indent=2)

    async def task_statuses_resource(self) -> str:
        """
        Provide information about available task statuses

        Returns:
            JSON string containing status definitions
        """
        try:
            # Get real-time status counts from database
            async with get_db_session() as db:
                status_counts = {}
                try:
                    # Get count by status
                    tasks_by_status = await task_crud.get_task_counts_by_status(db)
                    for task_info in tasks_by_status:
                        status_counts[task_info.status] = task_info.count
                except Exception as db_error:
                    logger.warning(f"Could not get status counts from DB: {db_error}")
                    status_counts = {}

            # Build status information
            status_info = MCPResourceDefinitions.TASK_STATUSES.copy()
            for status, info in status_info.items():
                info["count"] = status_counts.get(status, 0)
                info["description"] += f" (Current count: {status_counts.get(status, 0)})"

            # Add workflow information
            workflow = [
                {
                    "from_status": "PENDING",
                    "to_status": "PROCESSING",
                    "trigger": "AI worker picks up task",
                    "automatic": True
                },
                {
                    "from_status": "PROCESSING",
                    "to_status": "COMPLETED",
                    "trigger": "AI processing successful",
                    "automatic": True
                },
                {
                    "from_status": "PROCESSING",
                    "to_status": "FAILED",
                    "trigger": "AI processing error or timeout",
                    "automatic": True
                }
            ]

            return json.dumps({
                "statuses": status_info,
                "workflow": workflow,
                "total_tasks": sum(status_counts.values()),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }, indent=2)

        except Exception as e:
            logger.error(f"Error generating task statuses resource: {e}")
            return json.dumps({
                "error": str(e),
                "message": "Failed to generate task status information"
            }, indent=2)

    async def available_models_resource(self) -> str:
        """
        Provide information about available AI models

        Returns:
            JSON string containing model definitions and availability
        """
        try:
            models = MCPResourceDefinitions.AVAILABLE_MODELS.copy()

            # Add current usage statistics
            async with get_db_session() as db:
                try:
                    # Get model usage counts
                    model_usage = await task_crud.get_model_usage_stats(db)
                    for model_name, usage_info in model_usage.items():
                        # Add usage stats to model info
                        for model_key, model_info in models.items():
                            if model_info["name"] == model_name:
                                model_info["usage_stats"] = {
                                    "total_tasks": usage_info.total_tasks,
                                    "completed_tasks": usage_info.completed_tasks,
                                    "success_rate": (
                                        usage_info.completed_tasks / usage_info.total_tasks * 100
                                        if usage_info.total_tasks > 0
                                        else 0
                                    )
                                }
                                break
                except Exception as db_error:
                    logger.warning(f"Could not get model usage stats: {db_error}")

            # Add cost estimation for common task sizes
            for model_key, model_info in models.items():
                model_info["cost_estimates"] = {
                    "short_task": {
                        "tokens": 100,
                        "estimated_cost": model_info["cost_per_token"] * 100
                    },
                    "medium_task": {
                        "tokens": 1000,
                        "estimated_cost": model_info["cost_per_token"] * 1000
                    },
                    "long_task": {
                        "tokens": 5000,
                        "estimated_cost": model_info["cost_per_token"] * 5000
                    }
                }

            # Add model comparison
            comparison = {
                "cheapest": min(models.items(), key=lambda x: x[1]["cost_per_token"])[1]["name"],
                "largest_context": max(models.items(), key=lambda x: x[1]["context_window"])[1]["name"],
                "most_recommended": "deepseek-chat"  # Our default recommendation
            }

            return json.dumps({
                "models": models,
                "comparison": comparison,
                "default_model": mcp_settings.default_model,
                "default_provider": mcp_settings.default_provider,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }, indent=2)

        except Exception as e:
            logger.error(f"Error generating available models resource: {e}")
            return json.dumps({
                "error": str(e),
                "message": "Failed to generate model information"
            }, indent=2)

    async def system_stats_resource(self) -> str:
        """
        Provide system statistics and health information

        Returns:
            JSON string containing system statistics
        """
        try:
            async with get_db_session() as db:
                # Get overall statistics
                total_tasks = await task_crud.get_total_task_count(db)

                # Get status breakdown
                status_breakdown = {}
                try:
                    status_counts = await task_crud.get_task_counts_by_status(db)
                    for status_info in status_counts:
                        status_breakdown[status_info.status] = status_info.count
                except:
                    status_breakdown = {"error": "Could not retrieve status breakdown"}

                # Get recent activity (last 24 hours)
                recent_activity = {}
                try:
                    recent_tasks = await task_crud.get_recent_tasks(db, hours=24)
                    recent_activity = {
                        "tasks_last_24h": len(recent_tasks),
                        "completed_last_24h": len([t for t in recent_tasks if t.status == "COMPLETED"]),
                        "failed_last_24h": len([t for t in recent_tasks if t.status == "FAILED"])
                    }
                except:
                    recent_activity = {"error": "Could not retrieve recent activity"}

                # Calculate performance metrics
                performance_metrics = {}
                try:
                    avg_processing_time = await task_crud.get_average_processing_time(db)
                    success_rate = (
                        status_breakdown.get("COMPLETED", 0) / total_tasks * 100
                        if total_tasks > 0
                        else 0
                    )

                    performance_metrics = {
                        "average_processing_time_seconds": avg_processing_time,
                        "success_rate_percent": round(success_rate, 2),
                        "total_completed": status_breakdown.get("COMPLETED", 0),
                        "total_failed": status_breakdown.get("FAILED", 0)
                    }
                except:
                    performance_metrics = {"error": "Could not calculate performance metrics"}

            # System health indicators
            system_health = {
                "status": "healthy",
                "issues": [],
                "recommendations": []
            }

            # Check for potential issues
            if recent_activity.get("tasks_last_24h", 0) == 0:
                system_health["status"] = "warning"
                system_health["issues"].append("No tasks in the last 24 hours")
                system_health["recommendations"].append("Check if task creation is working properly")

            if performance_metrics.get("success_rate_percent", 0) < 80:
                system_health["status"] = "warning"
                system_health["issues"].append("Low success rate detected")
                system_health["recommendations"].append("Review AI model configurations and prompts")

            return json.dumps({
                "overview": {
                    "total_tasks": total_tasks,
                    "system_status": system_health["status"],
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                },
                "status_breakdown": status_breakdown,
                "recent_activity": recent_activity,
                "performance_metrics": performance_metrics,
                "system_health": system_health,
                "configuration": {
                    "max_tasks_per_request": mcp_settings.max_tasks_per_request,
                    "default_task_limit": mcp_settings.default_task_limit,
                    "default_model": mcp_settings.default_model,
                    "default_provider": mcp_settings.default_provider
                }
            }, indent=2)

        except Exception as e:
            logger.error(f"Error generating system stats resource: {e}")
            return json.dumps({
                "error": str(e),
                "message": "Failed to generate system statistics"
            }, indent=2)


# Resource instance
task_resources = TaskResourcesMixin()

# Export resource functions for direct access
async def task_schema_resource() -> str:
    """Task schema resource function"""
    return await task_resources.task_schema_resource()


async def task_statuses_resource() -> str:
    """Task statuses resource function"""
    return await task_resources.task_statuses_resource()


async def available_models_resource() -> str:
    """Available models resource function"""
    return await task_resources.available_models_resource()


async def system_stats_resource() -> str:
    """System stats resource function"""
    return await task_resources.system_stats_resource()


def get_resource_definitions() -> List[Dict[str, Any]]:
    """Get all resource definitions"""
    return [
        {
            "uri": "data://tasks/schema",
            "name": "Task Schema",
            "description": "JSON schema for task objects with validation rules and examples",
            "mime_type": "application/json"
        },
        {
            "uri": "data://tasks/statuses",
            "name": "Task Statuses",
            "description": "Available task statuses, counts, and workflow information",
            "mime_type": "application/json"
        },
        {
            "uri": "data://models/available",
            "name": "Available AI Models",
            "description": "Supported AI models with usage statistics and cost estimates",
            "mime_type": "application/json"
        },
        {
            "uri": "data://system/stats",
            "name": "System Statistics",
            "description": "System performance metrics, health indicators, and configuration",
            "mime_type": "application/json"
        }
    ]