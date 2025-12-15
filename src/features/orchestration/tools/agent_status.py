"""
MCP Tool: agent.status

Get status of active model instances.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.orchestration import AgentExecutor, ModelType, InstanceStatus, OrchestrationStorage


# Cache global para reutilizar executors
_executors: Dict[str, AgentExecutor] = {}


def _get_executor(project_path: Optional[str]) -> AgentExecutor:
    """
    Get or create AgentExecutor instance.

    Args:
        project_path: Optional project path

    Returns:
        AgentExecutor instance
    """
    key = project_path or "default"
    if key not in _executors:
        path = Path(project_path) if project_path else Path.cwd()
        storage = OrchestrationStorage(path)
        _executors[key] = AgentExecutor(storage)
    return _executors[key]


async def agent_status(
    instance_id: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    include_completed: bool = False,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get status of model instances.

    Can query a specific instance by ID, or filter by various criteria.

    Args:
        instance_id: Optional specific instance ID to query
        model: Optional filter by model type (haiku/sonnet/opus)
        status: Optional filter by status (pending/running/completed/failed)
        tags: Optional filter by tags
        include_completed: Include completed/failed instances (default False)
        project_path: Optional CFA project path

    Returns:
        Dictionary with:
            - instances: List of matching instances
            - summary: Aggregated statistics
            - token_usage: Total token usage by model

    Example:
        # Get all running instances
        result = await agent_status(status="running")

        # Get specific instance
        result = await agent_status(instance_id="abc-123")

        # Get all Opus instances
        result = await agent_status(model="opus")
    """
    try:
        # Get executor
        executor = _get_executor(project_path)

        # Convert string model to ModelType if provided
        model_type = None
        if model:
            model_map = {
                "haiku": ModelType.HAIKU,
                "sonnet": ModelType.SONNET,
                "opus": ModelType.OPUS
            }
            model_type = model_map.get(model.lower())

        # Convert string status to InstanceStatus if provided
        status_type = None
        if status:
            status_map = {
                "pending": InstanceStatus.PENDING,
                "running": InstanceStatus.RUNNING,
                "completed": InstanceStatus.COMPLETED,
                "failed": InstanceStatus.FAILED,
                "terminated": InstanceStatus.TERMINATED
            }
            status_type = status_map.get(status.lower())

        # Delegate to core executor
        result = executor.get_status(
            instance_id=instance_id,
            model=model_type,
            status=status_type,
            tags=tags,
            include_completed=include_completed
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get status: {str(e)}"
        }
