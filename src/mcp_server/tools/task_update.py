"""
MCP Tool: task.update

Update progress on current task.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.task_tracker import update_task, load_task, TaskStatus


async def task_update(
    project_path: str,
    completed_items: Optional[List[str]] = None,
    files_modified: Optional[List[str]] = None,
    blockers: Optional[List[str]] = None,
    next_steps: Optional[List[str]] = None,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update progress on the current task.

    Call this regularly to track:
    - What you've completed
    - Which files you've modified
    - Any blockers encountered
    - Updated next steps

    Args:
        project_path: Path to CFA project
        completed_items: Items you've finished (added to existing)
        files_modified: Files you've changed (added to existing)
        blockers: Current blockers (replaces existing)
        next_steps: Updated next steps (replaces existing)
        context: Updated context for next session

    Returns:
        Dictionary with:
            - success: Boolean
            - task: Updated task state
            - message: Human-readable status

    Example:
        result = await task_update(
            project_path="/projects/my-app",
            completed_items=["Added login endpoint to api.ts"],
            files_modified=["impl/api.ts"],
            next_steps=["Create JWT utility", "Add auth middleware"]
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
                "error": "No active task. Use task.start first."
            }

        task = update_task(
            project_path=project_path,
            completed_items=completed_items,
            files_modified=files_modified,
            blockers=blockers,
            next_steps=next_steps,
            context=context
        )

        return {
            "success": True,
            "task": {
                "goal": task.goal,
                "status": task.status.value,
                "completed": task.completed,
                "files_modified": task.files_modified,
                "blockers": task.blockers,
                "next_steps": task.next_steps
            },
            "file_updated": ".claude/current-task.md",
            "message": f"Task updated ({len(task.completed)} items done)"
        }

    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update task: {str(e)}"
        }
