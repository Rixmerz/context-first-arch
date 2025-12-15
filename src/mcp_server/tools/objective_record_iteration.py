"""
MCP Tool: objective.record_iteration

Record an iteration for an objective.
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


async def objective_record_iteration(
    objective_id: Optional[str] = None,
    summary: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record an iteration for the objective.

    Args:
        objective_id: Optional objective ID (uses active if not provided)
        summary: Optional summary of what was done in this iteration
        project_path: Optional CFA project path

    Returns:
        Dictionary with iteration count and status
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.record_iteration(
            objective_id=objective_id,
            summary=summary
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to record iteration: {str(e)}"
        }
