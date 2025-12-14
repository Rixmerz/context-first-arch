"""
MCP Tool: workflow.think_info

Reflect on collected information before proceeding.
"""

from typing import Any, Dict, List, Optional

from src.core.workflow.reflection import think_about_information


async def workflow_think_info(
    project_path: str,
    information: str,
    context: Optional[str] = None,
    questions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze and reflect on collected information.

    Provides a structured approach to analyzing information
    gathered during task execution, ensuring thoroughness
    before proceeding with implementation.

    Args:
        project_path: Path to the project root
        information: The information gathered so far
        context: Optional additional context
        questions: Specific questions to consider

    Returns:
        Dictionary with:
            - success: Boolean
            - information_summary: Summary of input information
            - task_context: Current task context
            - relevant_contracts: Contracts that may apply
            - reflection_template: Template for structured thinking
            - guidance: How to use the template

    Example:
        # After reading several files
        result = await workflow_think_info(
            project_path="/projects/my-app",
            information=\"\"\"
                Found these patterns in the codebase:
                - Auth uses JWT tokens stored in cookies
                - API routes follow REST conventions
                - Database uses SQLAlchemy ORM
            \"\"\",
            questions=[
                "Are there any existing auth middleware?",
                "What's the error handling pattern?"
            ]
        )

    Best Practice:
        Use this tool after gathering information but before
        making implementation decisions. It helps ensure you've
        considered all relevant aspects and aligned with contracts.
    """
    try:
        result = think_about_information(
            project_path=project_path,
            information=information,
            context=context,
            questions=questions
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Reflection failed: {str(e)}"
        }
