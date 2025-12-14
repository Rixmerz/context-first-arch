"""
MCP Tool: workflow.think_done

Evaluate whether a task is truly complete.
"""

from typing import Any, Dict

from src.core.workflow.reflection import think_about_completion


async def workflow_think_done(
    project_path: str,
    task_description: str,
    work_done: str,
    tests_passed: bool = False
) -> Dict[str, Any]:
    """
    Assess task completion thoroughly.

    Provides a comprehensive checklist for evaluating whether
    a task is truly complete before marking it done.

    Args:
        project_path: Path to the project root
        task_description: Original task description
        work_done: Summary of work completed
        tests_passed: Whether tests have passed (default: False)

    Returns:
        Dictionary with:
            - success: Boolean
            - task_description: The original task
            - work_summary: Summary of completed work
            - tests_passed: Test status
            - recorded_task: Task from current-task.md if exists
            - completion_checklist: Checklist for verification
            - preliminary_assessment: Initial completion assessment
            - guidance: How to use the checklist

    Example:
        # Before marking task complete
        result = await workflow_think_done(
            project_path="/projects/my-app",
            task_description="Add user authentication",
            work_done=\"\"\"
                Implemented:
                - Login endpoint with JWT generation
                - Logout endpoint with cookie clearing
                - Auth middleware for protected routes
                - Tests for all endpoints
            \"\"\",
            tests_passed=True
        )

        # Check the assessment
        if "appears ready" in result["preliminary_assessment"]:
            # Safe to mark complete
            pass

    Best Practice:
        Always run this before marking a task complete. It helps
        ensure nothing is forgotten and maintains quality standards.
        Pay special attention to:
        - Edge cases
        - Error handling
        - Documentation updates
        - Cleanup of debug code
    """
    try:
        result = think_about_completion(
            project_path=project_path,
            task_description=task_description,
            work_done=work_done,
            tests_passed=tests_passed
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Completion assessment failed: {str(e)}"
        }
