"""
MCP Tool: safe_point_rollback

Rollback to a previous safe point.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.features.orchestration import SafePointManager, OrchestrationStorage


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


async def safe_point_rollback(
    project_path: str,
    safe_point_id: Optional[str] = None,
    mode: str = "preview"
) -> Dict[str, Any]:
    """
    Rollback to a previous safe point.

    Args:
        project_path: Path to project root
        safe_point_id: ID of safe point to rollback to (optional, uses latest if not provided)
        mode: 'preview' to see changes, 'execute' to perform rollback (default 'preview')

    Returns:
        Dictionary with rollback result
    """
    try:
        # Validate inputs
        if not project_path:
            return {"success": False, "error": "project_path is required"}
        if mode not in ["preview", "execute"]:
            return {"success": False, "error": "mode must be 'preview' or 'execute'"}

        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.rollback(
            project_path=project_path,
            safe_point_id=safe_point_id,
            mode=mode
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Rollback failed: {str(e)}"
        }
