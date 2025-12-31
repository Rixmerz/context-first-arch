"""
MCP Tool: config.list_mcp_configs

List all MCP server configurations.
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


async def config_list_mcp_configs(
    include_disabled: bool = False,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all MCP server configurations.

    Args:
        include_disabled: Include disabled configs in the list
        project_path: Optional CFA project path

    Returns:
        Dictionary with list of MCP configurations
    """
    try:
        storage = _get_storage(project_path)
        configs = storage.list_mcp_configs(include_disabled=include_disabled)

        # Separate enabled and disabled for better visibility
        enabled_count = sum(1 for c in configs if c["enabled"])
        disabled_count = len(configs) - enabled_count

        return {
            "success": True,
            "configs": configs,
            "count": len(configs),
            "enabled_count": enabled_count,
            "disabled_count": disabled_count,
            "include_disabled": include_disabled
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list MCP configs: {str(e)}"
        }
