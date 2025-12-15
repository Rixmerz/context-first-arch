"""
MCP Tool: loop.configure

Configure an iterative execution loop.
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


async def loop_configure(
    task: str,
    condition_type: str = "objective_complete",
    max_iterations: int = 10,
    iteration_delay_ms: int = 1000,
    enable_safe_points: bool = True,
    escalation_threshold: int = 5,
    project_path: Optional[str] = None,
    objective_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configure a new iterative execution loop.

    Args:
        task: Task to work on iteratively
        condition_type: When to stop (objective_complete, all_checkpoints, manual)
        max_iterations: Maximum iterations before giving up
        iteration_delay_ms: Delay between iterations in milliseconds
        enable_safe_points: Create git commits after each iteration
        escalation_threshold: After this many iterations, escalate model
        project_path: Optional CFA project path
        objective_id: Optional objective to track

    Returns:
        Dictionary with loop configuration and instructions
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.configure(
            task=task,
            condition_type=condition_type,
            max_iterations=max_iterations,
            iteration_delay_ms=iteration_delay_ms,
            enable_safe_points=enable_safe_points,
            escalation_threshold=escalation_threshold,
            project_path=project_path,
            objective_id=objective_id
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to configure loop: {str(e)}"
        }
