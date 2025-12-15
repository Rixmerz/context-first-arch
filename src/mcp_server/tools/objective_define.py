"""
MCP Tool: objective.define

Define an end-to-end objective with success criteria and checkpoints.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, List, Optional
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


async def objective_define(
    description: str,
    success_criteria: Optional[List[str]] = None,
    checkpoints: Optional[List[str]] = None,
    max_iterations: int = 10,
    project_path: Optional[str] = None,
    tags: Optional[List[str]] = None,
    auto_activate: bool = True
) -> Dict[str, Any]:
    """
    Define a new objective with success criteria and checkpoints.

    Creates a trackable objective that can be worked on iteratively
    across multiple model interactions until completion.

    Args:
        description: Clear description of what needs to be accomplished
        success_criteria: List of specific criteria that define success
        checkpoints: Optional list of milestone descriptions
        max_iterations: Maximum iterations before objective fails (default 10)
        project_path: Optional CFA project path for context
        tags: Optional tags for organization
        auto_activate: Make this the active objective (default True)

    Returns:
        Dictionary with:
            - objective_id: Unique identifier
            - objective: Full objective details
            - checkpoints: Generated/provided checkpoints
            - message: Human-readable status

    Example:
        result = await objective_define(
            description="Implement user authentication with JWT",
            success_criteria=[
                "Users can register with email/password",
                "Users can login and receive JWT",
                "Protected routes require valid JWT",
                "Tokens expire after 24 hours"
            ],
            max_iterations=15
        )
    """
    try:
        # Get manager
        manager = _get_manager(project_path)

        # Delegate to core manager
        result = manager.define(
            description=description,
            success_criteria=success_criteria,
            checkpoints=checkpoints,
            max_iterations=max_iterations,
            project_path=project_path,
            tags=tags,
            auto_activate=auto_activate
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to define objective: {str(e)}"
        }
