"""
Workflow Feature - Session Onboarding

Load project context at the start of each session.

Note: Reflection and summarization tools removed.
Claude handles meta-cognition natively.
"""

from .core import generate_onboarding, check_onboarding_status

__all__ = [
    "generate_onboarding",
    "check_onboarding_status",
]
