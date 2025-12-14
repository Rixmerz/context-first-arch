"""
Workflow module for AI-assisted development.

Provides meta-cognitive tools for:
- Project onboarding
- Task reflection
- Progress validation
- Change summarization
"""

from src.core.workflow.onboarding import (
    generate_onboarding,
    check_onboarding_status,
)
from src.core.workflow.reflection import (
    think_about_information,
    think_about_task,
    think_about_completion,
    summarize_changes,
)

__all__ = [
    # Onboarding
    "generate_onboarding",
    "check_onboarding_status",
    # Reflection
    "think_about_information",
    "think_about_task",
    "think_about_completion",
    "summarize_changes",
]
