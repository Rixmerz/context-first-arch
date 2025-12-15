"""
MCP Tool: agent.spawn

Spawn a model instance via Claude Code Task Tool.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.orchestration import AgentExecutor, ModelType, OrchestrationStorage


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


async def agent_spawn(
    model: str,
    task: str,
    context: Optional[str] = None,
    project_path: Optional[str] = None,
    timeout: Optional[int] = 120000,
    max_tokens: Optional[int] = 8000,
    background: bool = False,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Spawn a new model instance to execute a task.

    This tool prepares spawn instructions for Claude Code's Task Tool.
    In production, this would actually invoke the Task Tool to create
    a subagent with the specified model.

    Args:
        model: Model type (haiku, sonnet, opus)
        task: The task for the model to execute
        context: Optional context to provide to the model
        project_path: Optional CFA project path for context enrichment
        timeout: Timeout in milliseconds (default 120000 = 2 minutes)
        max_tokens: Maximum tokens for response (default 8000)
        background: Run in background mode
        tags: Optional tags for tracking/filtering instances

    Returns:
        Dictionary with:
            - instance_id: Unique identifier for this instance
            - spawn_config: Configuration for Task Tool
            - status: Current status (pending/spawned)
            - message: Human-readable status

    Example:
        result = await agent_spawn(
            model="sonnet",
            task="Implement JWT authentication",
            context="Express.js backend, MongoDB database",
            timeout=180000
        )
    """
    try:
        # Convert string model to ModelType
        model_map = {
            "haiku": ModelType.HAIKU,
            "sonnet": ModelType.SONNET,
            "opus": ModelType.OPUS
        }
        model_type = model_map.get(model.lower())

        if not model_type:
            return {
                "success": False,
                "error": f"Invalid model: {model}. Valid models: haiku, sonnet, opus"
            }

        # Get executor
        executor = _get_executor(project_path)

        # Delegate to core executor
        result = executor.spawn(
            model=model_type,
            task=task,
            context=context,
            project_path=project_path,
            timeout_ms=timeout,
            max_tokens=max_tokens,
            background=background,
            tags=tags or []
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Spawn preparation failed: {str(e)}"
        }
