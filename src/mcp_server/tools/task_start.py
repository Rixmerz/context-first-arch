"""
MCP Tool: task.start

Start a new task in current-task.md.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.task_tracker import start_task, TaskStatus


async def task_start(
    project_path: str,
    goal: str,
    next_steps: Optional[List[str]] = None,
    context: str = ""
) -> Dict[str, Any]:
    """
    Start a new task and update current-task.md.

    This clears any previous task and starts fresh.
    Use this at the beginning of a work session.

    Args:
        project_path: Path to CFA project
        goal: What you're trying to accomplish (be specific)
        next_steps: Optional list of planned steps
        context: Any relevant background information

    Returns:
        Dictionary with:
            - success: Boolean
            - task: Current task state
            - message: Human-readable status

    Example:
        result = await task_start(
            project_path="/projects/my-app",
            goal="Implement user authentication with JWT",
            next_steps=[
                "Add login endpoint to api.ts",
                "Create JWT utility in shared/utils.ts",
                "Add auth middleware"
            ],
            context="Using jsonwebtoken library, tokens expire in 24h"
        )
    """
    try:
        claude_dir = Path(project_path) / ".claude"

        if not claude_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path} (missing .claude/)"
            }

        task = start_task(
            project_path=project_path,
            goal=goal,
            next_steps=next_steps,
            context=context
        )

        return {
            "success": True,
            "task": {
                "goal": task.goal,
                "status": task.status.value,
                "next_steps": task.next_steps,
                "context": task.context
            },
            "file_updated": ".claude/current-task.md",
            "message": f"Task started: {goal}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start task: {str(e)}"
        }
