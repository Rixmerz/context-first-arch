"""
MCP Tool: config.list_prompts

List all available system prompts.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.features.orchestration import OrchestrationStorage


# Cache global para reutilizar storage
_storage_cache: Dict[str, OrchestrationStorage] = {}


def _get_storage(project_path: Optional[str]) -> OrchestrationStorage:
    """Get or create OrchestrationStorage instance."""
    key = project_path or "default"
    if key not in _storage_cache:
        path = Path(project_path) if project_path else Path.cwd()
        _storage_cache[key] = OrchestrationStorage(path)
    return _storage_cache[key]


async def config_list_prompts(
    category: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all available system prompts.

    Args:
        category: Optional filter by category
        project_path: Optional CFA project path

    Returns:
        Dictionary with list of prompts
    """
    try:
        storage = _get_storage(project_path)
        prompts = storage.list_prompts(category=category)

        return {
            "success": True,
            "prompts": prompts,
            "count": len(prompts),
            "filter": {"category": category} if category else None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list prompts: {str(e)}"
        }
