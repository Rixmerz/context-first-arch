"""
MCP Tool: config.get_active

Get currently active configuration.
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


async def config_get_active(
    config_type: str = "all",
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get currently active configuration.

    Args:
        config_type: Type of config to get (prompts, mcp, all)
        project_path: Optional CFA project path

    Returns:
        Dictionary with active configuration
    """
    try:
        storage = _get_storage(project_path)

        # Validate config_type
        valid_types = ["prompts", "mcp", "all"]
        if config_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid config_type '{config_type}'. Must be one of: {valid_types}"
            }

        result: Dict[str, Any] = {
            "success": True,
            "config_type": config_type
        }

        # Get active prompts
        if config_type in ["prompts", "all"]:
            active_prompts = storage.get_active_prompts()
            result["prompts"] = {
                "active": active_prompts,
                "count": len(active_prompts)
            }

        # Get enabled MCP configs
        if config_type in ["mcp", "all"]:
            mcp_configs = storage.list_mcp_configs(include_disabled=False)
            result["mcp"] = {
                "enabled": mcp_configs,
                "count": len(mcp_configs)
            }

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get active config: {str(e)}"
        }
