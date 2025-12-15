"""
Workflow Core Module - Meta-cognition and Reflection

Provides structured thinking and workflow management.
"""

from .onboarding import generate_onboarding, check_onboarding_status
from .reflection import (
    think_about_information,
    think_about_task,
    think_about_completion,
    summarize_changes,
)

__all__ = [
    "generate_onboarding",
    "check_onboarding_status",
    "think_about_information",
    "think_about_task",
    "think_about_completion",
    "summarize_changes",
]
