"""
MCP Prompts Implementation

Prompt templates and generators exposed through Model Context Protocol
for external AI systems to generate contextual responses.
"""

from .task_prompts import (
    task_summary_prompt,
    system_health_prompt,
    task_analysis_prompt,
    performance_review_prompt
)

__all__ = [
    "task_summary_prompt",
    "system_health_prompt",
    "task_analysis_prompt",
    "performance_review_prompt"
]