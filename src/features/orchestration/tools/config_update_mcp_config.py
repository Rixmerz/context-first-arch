"""
MCP Tool: config.update_mcp_config

Update MCP server configuration.
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


async def config_update_mcp_config(
    server_name: str,
    config: Optional[Dict[str, Any]] = None,
    enabled: Optional[bool] = None,
    project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update MCP server configuration.

    Args:
        server_name: MCP server name
        config: Configuration object (optional)
        enabled: Enable/disable server (optional)
        project_path: Optional CFA project path

    Returns:
        Dictionary with operation result
    """
    try:
        storage = _get_storage(project_path)

        # Check if config exists
        existing = storage.get_mcp_config(server_name)

        if existing:
            # Update existing config
            updated = storage.update_mcp_config(
                server_name=server_name,
                config=config,
                enabled=enabled
            )
            if updated:
                result = storage.get_mcp_config(server_name)
                return {
                    "success": True,
                    "action": "updated",
                    "config": result
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update config"
                }
        else:
            # Create new config
            if config is None:
                return {
                    "success": False,
                    "error": f"Server '{server_name}' not found. Provide 'config' to create new."
                }

            storage.create_mcp_config(
                server_name=server_name,
                config=config,
                enabled=enabled if enabled is not None else True
            )
            result = storage.get_mcp_config(server_name)
            return {
                "success": True,
                "action": "created",
                "config": result
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update MCP config: {str(e)}"
        }
