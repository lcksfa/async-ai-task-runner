"""
Task Prompts for MCP

Prompt templates and generators for task analysis, summaries,
and system insights through Model Context Protocol.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.database import get_db_session
from app.crud import task as task_crud
from app.mcp.config import mcp_settings

logger = logging.getLogger(__name__)


class TaskPromptsMixin:
    """Mixin class providing task-related prompts"""

    async def task_summary_prompt(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a summary of task execution

        Args:
            arguments: Dictionary containing optional parameters:
                - task_ids (str, optional): Comma-separated list of task IDs
                - status_filter (str, optional): Filter by task status
                - time_range (str, optional): Time range like "24h", "7d", "1m"
                - include_results (bool, optional): Whether to include task results

        Returns:
            Dictionary with generated summary prompt
        """
        try:
            # Parse arguments
            args = arguments or {}
            task_ids_str = args.get("task_ids", "")
            status_filter = args.get("status_filter")
            time_range = args.get("time_range")
            include_results = args.get("include_results", False)

            # Get tasks
            async with get_db_session() as db:
                tasks = []

                if task_ids_str:
                    # Specific task IDs
                    try:
                        task_ids = [int(id.strip()) for id in task_ids_str.split(",") if id.strip()]
                        for task_id in task_ids:
                            task = await task_crud.get_task(db=db, task_id=task_id)
                            if task:
                                tasks.append(task)
                    except ValueError:
                        logger.warning(f"Invalid task IDs format: {task_ids_str}")

                elif status_filter or time_range:
                    # Filtered tasks
                    skip = 0
                    limit = mcp_settings.max_tasks_per_request

                    # Apply time range filter
                    if time_range:
                        if time_range.endswith("h"):
                            hours = int(time_range[:-1])
                            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                        elif time_range.endswith("d"):
                            days = int(time_range[:-1])
                            cutoff_time = datetime.utcnow() - timedelta(days=days)
                        elif time_range.endswith("m"):
                            minutes = int(time_range[:-1])
                            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
                        else:
                            cutoff_time = None
                    else:
                        cutoff_time = None

                    tasks = await task_crud.get_tasks_with_filters(
                        db=db,
                        skip=skip,
                        limit=limit,
                        status=status_filter,
                        created_after=cutoff_time
                    )

                else:
                    # Default to recent tasks
                    tasks = await task_crud.get_recent_tasks(db, hours=24, limit=50)

                # Generate summary data
                summary_data = self._generate_task_summary_data(tasks, include_results)

                # Build prompt template
                prompt_template = self._build_task_summary_prompt(summary_data, args)

                return {
                    "name": "task_summary",
                    "description": "Generate a summary of task execution and performance",
                    "arguments": {
                        "task_ids": task_ids_str if task_ids_str else "Not specified",
                        "status_filter": status_filter or "All statuses",
                        "time_range": time_range or "All time",
                        "include_results": include_results,
                        "total_tasks_analyzed": len(tasks)
                    },
                    "template": prompt_template,
                    "data": summary_data,
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }

        except Exception as e:
            logger.error(f"Error generating task summary prompt: {e}")
            return {
                "name": "task_summary",
                "error": str(e),
                "message": "Failed to generate task summary prompt"
            }

    async def system_health_prompt(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a system health report prompt

        Args:
            arguments: Dictionary containing optional parameters:
                - detailed (bool, optional): Include detailed diagnostics
                - recommendations (bool, optional): Include actionable recommendations
                - time_range (str, optional): Time range for analysis like "24h", "7d"

        Returns:
            Dictionary with generated health prompt
        """
        try:
            args = arguments or {}
            detailed = args.get("detailed", False)
            recommendations = args.get("recommendations", True)
            time_range = args.get("time_range", "24h")

            async with get_db_session() as db:
                # Get system health data
                health_data = await self._collect_system_health_data(db, time_range, detailed)

                # Generate health assessment
                health_assessment = self._assess_system_health(health_data)

                # Build prompt template
                prompt_template = self._build_system_health_prompt(
                    health_data, health_assessment, recommendations, detailed
                )

                return {
                    "name": "system_health",
                    "description": "Generate a comprehensive system health report",
                    "arguments": {
                        "detailed": detailed,
                        "recommendations": recommendations,
                        "time_range": time_range
                    },
                    "template": prompt_template,
                    "health_data": health_data,
                    "health_assessment": health_assessment,
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }

        except Exception as e:
            logger.error(f"Error generating system health prompt: {e}")
            return {
                "name": "system_health",
                "error": str(e),
                "message": "Failed to generate system health prompt"
            }

    async def task_analysis_prompt(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a task analysis prompt for deep insights

        Args:
            arguments: Dictionary containing optional parameters:
                - analysis_type (str, optional): Type of analysis (performance, errors, patterns)
                - task_ids (str, optional): Specific tasks to analyze
                - compare_models (bool, optional): Compare performance across models
                - time_range (str, optional): Time range for analysis

        Returns:
            Dictionary with generated analysis prompt
        """
        try:
            args = arguments or {}
            analysis_type = args.get("analysis_type", "performance")
            task_ids_str = args.get("task_ids", "")
            compare_models = args.get("compare_models", True)
            time_range = args.get("time_range", "7d")

            async with get_db_session() as db:
                # Get tasks for analysis
                tasks = await self._get_tasks_for_analysis(db, task_ids_str, time_range)

                # Perform analysis
                analysis_data = await self._perform_task_analysis(
                    db, tasks, analysis_type, compare_models
                )

                # Build prompt template
                prompt_template = self._build_task_analysis_prompt(
                    analysis_data, analysis_type, compare_models
                )

                return {
                    "name": "task_analysis",
                    "description": f"Generate {analysis_type} analysis of task execution",
                    "arguments": {
                        "analysis_type": analysis_type,
                        "task_ids": task_ids_str if task_ids_str else "Filtered tasks",
                        "compare_models": compare_models,
                        "time_range": time_range,
                        "tasks_analyzed": len(tasks)
                    },
                    "template": prompt_template,
                    "analysis_data": analysis_data,
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }

        except Exception as e:
            logger.error(f"Error generating task analysis prompt: {e}")
            return {
                "name": "task_analysis",
                "error": str(e),
                "message": "Failed to generate task analysis prompt"
            }

    async def performance_review_prompt(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a performance review prompt for system optimization

        Args:
            arguments: Dictionary containing optional parameters:
                - focus_area (str, optional): Focus area (speed, accuracy, cost, reliability)
                - benchmarking (bool, optional): Include benchmarking comparisons
                - recommendations_level (str, optional): Level of recommendations (basic, detailed, expert)
                - time_range (str, optional): Time range for review

        Returns:
            Dictionary with generated performance review prompt
        """
        try:
            args = arguments or {}
            focus_area = args.get("focus_area", "overall")
            benchmarking = args.get("benchmarking", True)
            recommendations_level = args.get("recommendations_level", "detailed")
            time_range = args.get("time_range", "7d")

            async with get_db_session() as db:
                # Collect performance data
                performance_data = await self._collect_performance_data(
                    db, focus_area, time_range, benchmarking
                )

                # Generate performance insights
                performance_insights = self._generate_performance_insights(
                    performance_data, focus_area, recommendations_level
                )

                # Build prompt template
                prompt_template = self._build_performance_review_prompt(
                    performance_data, performance_insights, focus_area, benchmarking
                )

                return {
                    "name": "performance_review",
                    "description": f"Generate performance review focused on {focus_area}",
                    "arguments": {
                        "focus_area": focus_area,
                        "benchmarking": benchmarking,
                        "recommendations_level": recommendations_level,
                        "time_range": time_range
                    },
                    "template": prompt_template,
                    "performance_data": performance_data,
                    "performance_insights": performance_insights,
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }

        except Exception as e:
            logger.error(f"Error generating performance review prompt: {e}")
            return {
                "name": "performance_review",
                "error": str(e),
                "message": "Failed to generate performance review prompt"
            }

    def _generate_task_summary_data(
        self, tasks: List[Any], include_results: bool
    ) -> Dict[str, Any]:
        """Generate summary data from tasks"""
        status_counts = {"PENDING": 0, "PROCESSING": 0, "COMPLETED": 0, "FAILED": 0}
        model_performance = {}
        provider_performance = {}
        priority_distribution = {}

        total_processing_time = 0
        completed_tasks = 0
        recent_tasks = []

        for task in tasks:
            # Status counts
            if task.status in status_counts:
                status_counts[task.status] += 1

            # Model performance
            if task.model not in model_performance:
                model_performance[task.model] = {"total": 0, "completed": 0, "failed": 0}
            model_performance[task.model]["total"] += 1
            if task.status == "COMPLETED":
                model_performance[task.model]["completed"] += 1
            elif task.status == "FAILED":
                model_performance[task.model]["failed"] += 1

            # Provider performance
            if task.provider not in provider_performance:
                provider_performance[task.provider] = {"total": 0, "completed": 0, "failed": 0}
            provider_performance[task.provider]["total"] += 1
            if task.status == "COMPLETED":
                provider_performance[task.provider]["completed"] += 1
            elif task.status == "FAILED":
                provider_performance[task.provider]["failed"] += 1

            # Priority distribution
            priority_key = f"Priority_{task.priority}"
            priority_distribution[priority_key] = priority_distribution.get(priority_key, 0) + 1

            # Processing time analysis
            if task.status == "COMPLETED" and task.created_at and task.updated_at:
                processing_time = (task.updated_at - task.created_at).total_seconds()
                total_processing_time += processing_time
                completed_tasks += 1

            # Recent tasks (last 10)
            if len(recent_tasks) < 10:
                recent_tasks.append({
                    "id": task.id,
                    "prompt": task.prompt[:100] + "..." if len(task.prompt) > 100 else task.prompt,
                    "status": task.status,
                    "model": task.model,
                    "provider": task.provider,
                    "priority": task.priority,
                    "result": task.result[:200] + "..." if (include_results and task.result and len(task.result) > 200) else (task.result if include_results and task.result else None)
                })

        avg_processing_time = total_processing_time / completed_tasks if completed_tasks > 0 else 0

        return {
            "overview": {
                "total_tasks": len(tasks),
                "status_breakdown": status_counts,
                "average_processing_time_seconds": round(avg_processing_time, 2),
                "completion_rate": round((status_counts["COMPLETED"] / len(tasks) * 100) if len(tasks) > 0 else 0, 2)
            },
            "model_performance": model_performance,
            "provider_performance": provider_performance,
            "priority_distribution": priority_distribution,
            "recent_tasks": recent_tasks
        }

    def _build_task_summary_prompt(
        self, summary_data: Dict[str, Any], args: Dict[str, Any]
    ) -> str:
        """Build task summary prompt template"""
        return f"""
You are analyzing the performance of an Async AI Task Runner system. Below is a summary of recent task execution data.

## Task Overview
- Total Tasks Analyzed: {summary_data['overview']['total_tasks']}
- Completion Rate: {summary_data['overview']['completion_rate']}%
- Average Processing Time: {summary_data['overview']['average_processing_time_seconds']} seconds

## Status Breakdown
- PENDING: {summary_data['overview']['status_breakdown']['PENDING']}
- PROCESSING: {summary_data['overview']['status_breakdown']['PROCESSING']}
- COMPLETED: {summary_data['overview']['status_breakdown']['COMPLETED']}
- FAILED: {summary_data['overview']['status_breakdown']['FAILED']}

## Model Performance
{self._format_performance_table(summary_data['model_performance'], 'Model')}

## Provider Performance
{self._format_performance_table(summary_data['provider_performance'], 'Provider')}

## Priority Distribution
{self._format_priority_distribution(summary_data['priority_distribution'])}

## Recent Tasks (Sample)
{self._format_recent_tasks(summary_data['recent_tasks'])}

## Analysis Request
Filter Criteria:
- Task IDs: {args.get('task_ids', 'Not specified')}
- Status Filter: {args.get('status_filter', 'All statuses')}
- Time Range: {args.get('time_range', 'All time')}
- Include Results: {args.get('include_results', False)}

Please provide:
1. A concise summary of system performance
2. Key insights and observations
3. Potential issues or concerns
4. Recommendations for improvement

Focus on patterns, anomalies, and actionable insights that could help optimize the task processing system.
        """

    def _assess_system_health(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall system health"""
        assessment = {
            "overall_status": "healthy",
            "score": 100,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }

        # Check completion rate
        completion_rate = health_data["performance"]["completion_rate"]
        if completion_rate < 90:
            assessment["issues"].append(f"Low completion rate: {completion_rate}%")
            assessment["score"] -= 20
        elif completion_rate < 95:
            assessment["warnings"].append(f"Moderate completion rate: {completion_rate}%")
            assessment["score"] -= 10

        # Check processing time
        avg_time = health_data["performance"]["average_processing_time"]
        if avg_time > 300:  # 5 minutes
            assessment["issues"].append(f"Slow average processing time: {avg_time}s")
            assessment["score"] -= 15
        elif avg_time > 180:  # 3 minutes
            assessment["warnings"].append(f"Moderate processing time: {avg_time}s")
            assessment["score"] -= 5

        # Check error rate
        error_rate = health_data["performance"]["error_rate"]
        if error_rate > 10:
            assessment["issues"].append(f"High error rate: {error_rate}%")
            assessment["score"] -= 25
        elif error_rate > 5:
            assessment["warnings"].append(f"Moderate error rate: {error_rate}%")
            assessment["score"] -= 10

        # Check for no recent activity
        recent_activity = health_data.get("recent_activity", {})
        if recent_activity.get("tasks_last_24h", 0) == 0:
            assessment["issues"].append("No activity in last 24 hours")
            assessment["score"] -= 30

        # Determine overall status
        if assessment["score"] >= 90:
            assessment["overall_status"] = "healthy"
        elif assessment["score"] >= 70:
            assessment["overall_status"] = "warning"
        else:
            assessment["overall_status"] = "critical"

        return assessment

    def _format_performance_table(self, performance_data: Dict[str, Any], label: str) -> str:
        """Format performance data as a table"""
        if not performance_data:
            return f"No {label.lower()} data available."

        lines = [f"| {label} | Total | Completed | Failed | Success Rate |"]
        lines.append("|" + "-" * (len(label) + 35) + "|")

        for name, stats in performance_data.items():
            success_rate = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            lines.append(f"| {name} | {stats['total']} | {stats['completed']} | {stats['failed']} | {success_rate:.1f}% |")

        return "\n".join(lines)

    def _format_priority_distribution(self, priority_data: Dict[str, Any]) -> str:
        """Format priority distribution"""
        if not priority_data:
            return "No priority data available."

        lines = ["Priority Distribution:"]
        for priority, count in sorted(priority_data.items()):
            lines.append(f"- {priority}: {count}")

        return "\n".join(lines)

    def _format_recent_tasks(self, recent_tasks: List[Dict[str, Any]]) -> str:
        """Format recent tasks"""
        if not recent_tasks:
            return "No recent tasks to display."

        lines = ["Recent Tasks:"]
        for task in recent_tasks:
            lines.append(f"ID {task['id']} [{task['status']}] ({task['model']}/{task['provider']}): {task['prompt']}")

        return "\n".join(lines)


# Prompt instance
task_prompts = TaskPromptsMixin()

# Export prompt functions for direct access
async def task_summary_prompt(arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Task summary prompt function"""
    return await task_prompts.task_summary_prompt(arguments)


async def system_health_prompt(arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """System health prompt function"""
    return await task_prompts.system_health_prompt(arguments)


async def task_analysis_prompt(arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Task analysis prompt function"""
    return await task_prompts.task_analysis_prompt(arguments)


async def performance_review_prompt(arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Performance review prompt function"""
    return await task_prompts.performance_review_prompt(arguments)


def get_prompt_definitions() -> List[Dict[str, Any]]:
    """Get all prompt definitions"""
    return [
        {
            "name": "task_summary",
            "description": "Generate a summary of task execution and performance",
            "arguments": [
                {
                    "name": "task_ids",
                    "description": "Comma-separated list of task IDs to analyze",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "status_filter",
                    "description": "Filter tasks by status (PENDING, PROCESSING, COMPLETED, FAILED)",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "time_range",
                    "description": "Time range for analysis (e.g., 24h, 7d, 1m)",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "include_results",
                    "description": "Include task results in summary",
                    "required": False,
                    "type": "boolean"
                }
            ]
        },
        {
            "name": "system_health",
            "description": "Generate a comprehensive system health report",
            "arguments": [
                {
                    "name": "detailed",
                    "description": "Include detailed diagnostics and metrics",
                    "required": False,
                    "type": "boolean",
                    "default": False
                },
                {
                    "name": "recommendations",
                    "description": "Include actionable recommendations",
                    "required": False,
                    "type": "boolean",
                    "default": True
                },
                {
                    "name": "time_range",
                    "description": "Time range for health analysis",
                    "required": False,
                    "type": "string",
                    "default": "24h"
                }
            ]
        },
        {
            "name": "task_analysis",
            "description": "Generate deep analysis of task execution patterns",
            "arguments": [
                {
                    "name": "analysis_type",
                    "description": "Type of analysis to perform",
                    "required": False,
                    "type": "string",
                    "enum": ["performance", "errors", "patterns", "usage"],
                    "default": "performance"
                },
                {
                    "name": "task_ids",
                    "description": "Specific task IDs to analyze",
                    "required": False,
                    "type": "string"
                },
                {
                    "name": "compare_models",
                    "description": "Compare performance across different AI models",
                    "required": False,
                    "type": "boolean",
                    "default": True
                },
                {
                    "name": "time_range",
                    "description": "Time range for analysis",
                    "required": False,
                    "type": "string",
                    "default": "7d"
                }
            ]
        },
        {
            "name": "performance_review",
            "description": "Generate performance review with optimization recommendations",
            "arguments": [
                {
                    "name": "focus_area",
                    "description": "Specific area to focus the review on",
                    "required": False,
                    "type": "string",
                    "enum": ["speed", "accuracy", "cost", "reliability", "overall"],
                    "default": "overall"
                },
                {
                    "name": "benchmarking",
                    "description": "Include benchmarking comparisons",
                    "required": False,
                    "type": "boolean",
                    "default": True
                },
                {
                    "name": "recommendations_level",
                    "description": "Level of detail for recommendations",
                    "required": False,
                    "type": "string",
                    "enum": ["basic", "detailed", "expert"],
                    "default": "detailed"
                },
                {
                    "name": "time_range",
                    "description": "Time range for performance review",
                    "required": False,
                    "type": "string",
                    "default": "7d"
                }
            ]
        }
    ]