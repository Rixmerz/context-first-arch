"""
MCP Tool: safe_point_create

Create a git safe point as restore point.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.orchestration import SafePointManager, OrchestrationStorage


# Cache global para reutilizar managers
_managers: Dict[str, SafePointManager] = {}


def _get_manager(project_path: Optional[str]) -> SafePointManager:
    """
    Get or create SafePointManager instance.

    Args:
        project_path: Optional project path

    Returns:
        SafePointManager instance
    """
    key = project_path or "default"
    if key not in _managers:
        path = Path(project_path) if project_path else Path.cwd()
        storage = OrchestrationStorage(path)
        _managers[key] = SafePointManager(storage)
    return _managers[key]


async def safe_point_create(
    project_path: str,
    task_summary: str,
    files_changed: Optional[List[str]] = None,
    include_untracked: bool = True,
    dry_run: bool = False,
    prefix: str = "[Nova]"
) -> Dict[str, Any]:
    """
    Create a git commit as a safe point.

    Args:
        project_path: Path to project root (must be git repo)
        task_summary: Summary of what was accomplished
        files_changed: Specific files to commit (optional)
        include_untracked: Include untracked files (default True)
        dry_run: Preview without committing (default False)
        prefix: Commit message prefix (default '[Nova]')

    Returns:
        Dictionary with safe point creation result
    """
    try:
        # Validate inputs
        if not project_path:
            return {"success": False, "error": "project_path is required"}
        if not task_summary:
            return {"success": False, "error": "task_summary is required"}

        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.create(
            project_path=project_path,
            task_summary=task_summary,
            files_changed=files_changed,
            include_untracked=include_untracked,
            dry_run=dry_run,
            prefix=prefix
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Safe point creation failed: {str(e)}"
        }
