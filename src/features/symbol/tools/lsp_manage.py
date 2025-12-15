"""
MCP Tool: lsp.status and lsp.restart

Manage LSP servers for semantic code analysis.
"""

from typing import Any, Dict, Optional

from src.features.symbol.core.manager import get_lsp_manager


async def lsp_status(project_path: str) -> Dict[str, Any]:
    """
    Get the status of LSP servers for a project.

    Returns information about which language servers are running,
    their health status, and supported languages.

    Args:
        project_path: Path to the project root

    Returns:
        Dictionary with:
            - success: Boolean
            - initialized: Whether LSP has been initialized
            - lsp_available: Whether LSP libraries are installed
            - project_path: Project being analyzed
            - active_servers: List of running language servers
            - supported_extensions: List of supported file extensions

    Example:
        result = await lsp_status(project_path="/projects/my-app")

        # Output:
        # {
        #     "success": True,
        #     "initialized": True,
        #     "lsp_available": True,
        #     "project_path": "/projects/my-app",
        #     "active_servers": ["python", "typescript"],
        #     "supported_extensions": [".py", ".ts", ".tsx", ".js", ".jsx", ...]
        # }
    """
    try:
        manager = get_lsp_manager(project_path)
        status = manager.get_status()

        return {
            "success": True,
            **status
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get LSP status: {str(e)}"
        }


async def lsp_restart(
    project_path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Restart LSP server(s) for a project.

    Use this when:
    - LSP seems to be returning stale results
    - After major codebase changes
    - After installing new dependencies
    - When symbol operations are failing

    Args:
        project_path: Path to the project root
        language: Specific language to restart ("python", "typescript", etc.)
                  If not specified, restarts all language servers

    Returns:
        Dictionary with:
            - success: Boolean
            - restarted: List of restarted language servers
            - failed: List of servers that failed to restart with errors
            - message: Human-readable status

    Example:
        # Restart all LSP servers
        result = await lsp_restart(project_path="/projects/my-app")

        # Restart only Python server
        result = await lsp_restart(
            project_path="/projects/my-app",
            language="python"
        )

        # Output:
        # {
        #     "success": True,
        #     "restarted": ["python"],
        #     "failed": [],
        #     "message": "LSP servers restarted successfully"
        # }
    """
    try:
        manager = get_lsp_manager(project_path)
        result = manager.restart(language=language)

        if result["success"]:
            restarted = result.get("restarted", [])
            if restarted:
                message = f"Restarted: {', '.join(restarted)}"
            else:
                message = "No servers to restart"
        else:
            failed = result.get("failed", [])
            message = f"Some servers failed to restart: {failed}"

        return {
            "success": result["success"],
            "restarted": result.get("restarted", []),
            "failed": result.get("failed", []),
            "message": message
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to restart LSP: {str(e)}"
        }
