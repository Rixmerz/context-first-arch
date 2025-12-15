"""
MCP Tool: loop.status

Get status of loops.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.features.orchestration import LoopManager, ObjectiveManager, OrchestrationStorage


# Cache global para reutilizar managers
_managers: Dict[str, LoopManager] = {}


def _get_manager(project_path: Optional[str]) -> LoopManager:
    """
    Get or create LoopManager instance.

    Args:
        project_path: Optional project path

    Returns:
        LoopManager instance
    """
    key = project_path or "default"
    if key not in _managers:
        path = Path(project_path) if project_path else Path.cwd()
        storage = OrchestrationStorage(path)
        objective_manager = ObjectiveManager(storage)
        _managers[key] = LoopManager(storage, objective_manager)
    return _managers[key]


async def loop_status(
    loop_id: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get status of loops.

    Args:
        loop_id: Optional specific loop ID to query
        project_path: Optional CFA project path

    Returns:
        Dictionary with loop status or summary of all loops
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.get_status(loop_id=loop_id)

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Status check failed: {str(e)}"
        }
