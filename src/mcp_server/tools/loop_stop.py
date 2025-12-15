"""
MCP Tool: loop.stop

Stop a running loop.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.orchestration import LoopManager, ObjectiveManager, OrchestrationStorage


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


async def loop_stop(
    loop_id: str,
    reason: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stop a running loop.

    Args:
        loop_id: ID of the loop to stop
        reason: Optional reason for stopping
        project_path: Optional CFA project path

    Returns:
        Dictionary with stop result
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.stop(
            loop_id=loop_id,
            reason=reason
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Stop failed: {str(e)}"
        }
