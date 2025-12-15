"""
MCP Tool: objective.achieve_checkpoint

Mark a checkpoint as achieved.
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


async def objective_achieve_checkpoint(
    checkpoint_id: str,
    objective_id: Optional[str] = None,
    notes: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark a checkpoint as achieved.

    Args:
        checkpoint_id: ID of checkpoint to mark as achieved
        objective_id: Optional objective ID (uses active if not provided)
        notes: Optional notes about how it was achieved
        project_path: Optional CFA project path

    Returns:
        Dictionary with updated progress
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.achieve_checkpoint(
            checkpoint_id=checkpoint_id,
            objective_id=objective_id,
            notes=notes
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to achieve checkpoint: {str(e)}"
        }
