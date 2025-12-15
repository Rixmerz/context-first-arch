"""
MCP Tool: safe_point_list

List available safe points.
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


async def safe_point_list(
    project_path: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List available safe points.

    Args:
        project_path: Optional project path (uses cwd if not provided)
        limit: Maximum number of safe points to return (default 10)

    Returns:
        Dictionary with list of safe points
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.list_safe_points(
            project_path=project_path,
            limit=limit
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list safe points: {str(e)}"
        }
