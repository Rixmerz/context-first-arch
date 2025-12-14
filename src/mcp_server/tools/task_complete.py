"""
MCP Tool: task.complete

Mark current task as completed.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.task_tracker import complete_task, load_task


async def task_complete(
    project_path: str,
    summary: str = ""
) -> Dict[str, Any]:
    """
    Mark the current task as completed.

    Clears blockers and next_steps, sets status to COMPLETED.
    Optionally adds a summary to context for future reference.

    Args:
        project_path: Path to CFA project
        summary: Optional summary of what was accomplished

    Returns:
        Dictionary with:
            - success: Boolean
            - task: Final task state
            - suggestion: Optional suggestion for next action

    Example:
        result = await task_complete(
            project_path="/projects/my-app",
            summary="Auth system complete. Login/logout working with JWT."
        )
    """
    try:
        claude_dir = Path(project_path) / ".claude"

        if not claude_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path}"
            }

        current = load_task(project_path)
        if current is None:
            return {
                "success": False,
                "error": "No active task to complete."
            }

        task = complete_task(project_path, summary)

        return {
            "success": True,
            "task": {
                "goal": task.goal,
                "status": task.status.value,
                "completed": task.completed,
                "files_modified": task.files_modified
            },
            "file_updated": ".claude/current-task.md",
            "suggestion": "Consider running project.scan to update map.md with changes",
            "message": f"Task completed: {task.goal}"
        }

    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to complete task: {str(e)}"
        }
