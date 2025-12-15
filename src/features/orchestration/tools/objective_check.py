"""
MCP Tool: objective.check

Check progress on an objective.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.features.orchestration import ObjectiveManager, OrchestrationStorage


# Cache global para reutilizar managers
_managers: Dict[str, ObjectiveManager] = {}


def _get_manager(project_path: Optional[str]) -> ObjectiveManager:
    """
    Get or create ObjectiveManager instance.

    Args:
        project_path: Optional project path

    Returns:
        ObjectiveManager instance
    """
    key = project_path or "default"
    if key not in _managers:
        path = Path(project_path) if project_path else Path.cwd()
        storage = OrchestrationStorage(path)
        _managers[key] = ObjectiveManager(storage)
    return _managers[key]


async def objective_check(
    objective_id: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check progress on an objective.

    Args:
        objective_id: Optional specific objective ID (uses active if not provided)
        project_path: Optional CFA project path

    Returns:
        Dictionary with:
            - progress: Progress percentage
            - checkpoints: Checkpoint status
            - status: Objective status
            - estimated_remaining: Estimated iterations remaining

    Example:
        result = await objective_check()
        # Returns progress report for active objective
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.check_progress(objective_id=objective_id)

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Check failed: {str(e)}"
        }
