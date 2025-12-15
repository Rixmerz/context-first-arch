"""
MCP Tool: objective.fail

Mark an objective as failed.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.orchestration import ObjectiveManager, OrchestrationStorage


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


async def objective_fail(
    reason: str,
    objective_id: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark an objective as failed.

    Args:
        reason: Reason for failure
        objective_id: Optional objective ID (uses active if not provided)
        project_path: Optional CFA project path

    Returns:
        Dictionary with failure result
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.mark_failed(
            reason=reason,
            objective_id=objective_id
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to mark objective as failed: {str(e)}"
        }
