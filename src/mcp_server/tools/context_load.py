"""
MCP Tool: context.load

Load full project context in a single call.
"""

from typing import Any, Dict
from pathlib import Path


async def context_load(project_path: str) -> Dict[str, Any]:
    """
    Load complete project context for LLM consumption.

    This is the OPTIMAL way to start working on a CFA project.
    Returns map.md + current-task.md content in ONE call.

    Args:
        project_path: Path to CFA project

    Returns:
        Dictionary with:
            - success: Boolean
            - map: Contents of map.md (project overview)
            - task: Contents of current-task.md (current state)
            - quick_stats: File counts and status

    Example:
        result = await context_load("/projects/my-app")
        # Now you have full context without multiple reads

    Why this matters:
        - Traditional: Read map.md (1 call) + Read task.md (1 call) = 2 calls
        - CFA: context.load = 1 call with everything needed
    """
    try:
        path = Path(project_path)
        claude_dir = path / ".claude"

        if not claude_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path} (missing .claude/)"
            }

        # Read core context files
        map_file = claude_dir / "map.md"
        task_file = claude_dir / "current-task.md"

        map_content = map_file.read_text() if map_file.exists() else "(no map.md)"
        task_content = task_file.read_text() if task_file.exists() else "(no current-task.md)"

        # Quick stats
        impl_files = list((path / "impl").glob("*")) if (path / "impl").exists() else []
        contract_files = list((path / "contracts").glob("*.contract.md")) if (path / "contracts").exists() else []

        return {
            "success": True,
            "map": map_content,
            "task": task_content,
            "quick_stats": {
                "impl_files": len([f for f in impl_files if f.is_file()]),
                "contracts": len(contract_files),
                "has_active_task": "IN_PROGRESS" in task_content or "BLOCKED" in task_content
            },
            "files_for_reference": {
                "map": ".claude/map.md",
                "task": ".claude/current-task.md",
                "decisions": ".claude/decisions.md"
            },
            "message": "Context loaded. You now have full project understanding."
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load context: {str(e)}"
        }
