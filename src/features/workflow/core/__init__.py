"""
Workflow Core Module - Session Onboarding

Provides project context loading at session start.
"""

from .onboarding import generate_onboarding, check_onboarding_status

__all__ = [
    "generate_onboarding",
    "check_onboarding_status",
]
