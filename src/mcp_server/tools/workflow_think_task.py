"""
MCP Tool: workflow.think_task

Evaluate adherence to task requirements.
"""

from typing import Any, Dict, List, Optional

from src.core.workflow.reflection import think_about_task


async def workflow_think_task(
    project_path: str,
    task_description: str,
    current_approach: str,
    concerns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate current approach against task requirements.

    Provides structured evaluation of implementation approach
    to ensure alignment with task requirements and project
    architecture.

    Args:
        project_path: Path to the project root
        task_description: Description of the task being worked on
        current_approach: The implementation approach being taken
        concerns: Any specific concerns to address

    Returns:
        Dictionary with:
            - success: Boolean
            - task_summary: Summary of the task
            - approach_summary: Summary of current approach
            - contracts_to_check: Relevant contracts for validation
            - has_decisions: Whether decisions.md exists
            - validation_template: Template for validation
            - guidance: How to use the template

    Example:
        # Before implementing a feature
        result = await workflow_think_task(
            project_path="/projects/my-app",
            task_description="Add user authentication with JWT",
            current_approach=\"\"\"
                Planning to:
                1. Add auth middleware
                2. Create login/logout endpoints
                3. Store tokens in httpOnly cookies
            \"\"\",
            concerns=[
                "Should we use refresh tokens?",
                "How to handle session expiration?"
            ]
        )

    Best Practice:
        Use this tool when you have a planned approach but want
        to validate it against project requirements before coding.
        It helps prevent scope creep and ensures contract compliance.
    """
    try:
        result = think_about_task(
            project_path=project_path,
            task_description=task_description,
            current_approach=current_approach,
            concerns=concerns
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Task validation failed: {str(e)}"
        }
