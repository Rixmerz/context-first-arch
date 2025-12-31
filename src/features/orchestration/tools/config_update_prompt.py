"""
MCP Tool: config.update_prompt

Update or create a system prompt.
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


async def config_update_prompt(
    prompt_id: str,
    content: str,
    category: Optional[str] = None,
    description: Optional[str] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update or create a system prompt.

    Args:
        prompt_id: Unique prompt identifier
        content: Prompt content
        category: Optional prompt category
        description: Optional prompt description
        project_path: Optional CFA project path

    Returns:
        Dictionary with operation result
    """
    try:
        storage = _get_storage(project_path)

        # Check if prompt exists (for is_new flag)
        existing = storage.get_prompt(prompt_id)
        is_new = existing is None

        # Create or update
        storage.create_prompt(
            prompt_id=prompt_id,
            content=content,
            category=category,
            description=description
        )

        # Get updated prompt
        updated = storage.get_prompt(prompt_id)

        return {
            "success": True,
            "action": "created" if is_new else "updated",
            "prompt": updated
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update prompt: {str(e)}"
        }
