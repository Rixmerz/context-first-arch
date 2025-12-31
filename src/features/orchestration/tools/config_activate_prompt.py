"""
MCP Tool: config.activate_prompt

Activate a system prompt for use.
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


async def config_activate_prompt(
    prompt_id: str,
    scope: str = "project",
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Activate a system prompt for use.

    Args:
        prompt_id: Prompt ID to activate
        scope: Activation scope (global, project, session)
        project_path: Optional CFA project path

    Returns:
        Dictionary with operation result
    """
    try:
        storage = _get_storage(project_path)

        # Verify prompt exists
        prompt = storage.get_prompt(prompt_id)
        if not prompt:
            return {
                "success": False,
                "error": f"Prompt '{prompt_id}' not found"
            }

        # Validate scope
        valid_scopes = ["global", "project", "session"]
        if scope not in valid_scopes:
            return {
                "success": False,
                "error": f"Invalid scope '{scope}'. Must be one of: {valid_scopes}"
            }

        # Activate prompt
        activated = storage.activate_prompt(prompt_id, scope=scope)

        if activated:
            updated_prompt = storage.get_prompt(prompt_id)
            return {
                "success": True,
                "message": f"Prompt '{prompt_id}' activated with scope '{scope}'",
                "prompt": updated_prompt
            }
        else:
            return {
                "success": False,
                "error": "Failed to activate prompt"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to activate prompt: {str(e)}"
        }
