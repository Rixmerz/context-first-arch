"""
MCP Tool: loop.iterate

Advance to the next iteration of a loop.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, List, Optional
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


async def loop_iterate(
    loop_id: str,
    iteration_result: Optional[str] = None,
    files_changed: Optional[List[str]] = None,
    tokens_used: int = 0,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Advance to the next iteration of a loop.

    Args:
        loop_id: ID of the loop to iterate
        iteration_result: Optional summary of previous iteration
        files_changed: Optional list of files changed
        tokens_used: Tokens used in previous iteration
        project_path: Optional CFA project path

    Returns:
        Dictionary with iteration status and context
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.iterate(
            loop_id=loop_id,
            iteration_result=iteration_result,
            files_changed=files_changed,
            tokens_used=tokens_used
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Iteration failed: {str(e)}"
        }
